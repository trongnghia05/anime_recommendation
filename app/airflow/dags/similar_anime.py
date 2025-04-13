import os
import sys

sys.path.append('/opt/airflow')
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
import json
import mlflow
import mlflow.pyfunc
import cloudpickle
import sklearn
import gensim
from airflow import DAG
from airflow.operators.python import PythonOperator
from gensim.models import Word2Vec
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from src.mlflow_utils import setup_mlflow, log_model_to_mlflow, evaluate_and_log_metrics

# Cấu hình MLflow để sử dụng MinIO
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://minio:9000"  # URL của MinIO server
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"  # Thay thế bằng credentials thực tế
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin"  # Thay thế bằng credentials thực tế
MLFLOW_TRACKING_URI = os.environ.get('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
API_SERVERS = json.loads(os.environ.get('API_SERVERS', '["http://fastapi:8000"]'))
MLFLOW_EXPERIMENT_NAME = "anime_recommendation_system_similar"

# Định nghĩa các tham số mặc định cho DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Tạo DAG
dag = DAG(
    'anime_recommendation_model_training',
    default_args=default_args,
    description='DAG huấn luyện mô hình đề xuất anime dựa trên dữ liệu từ database',
    schedule_interval=timedelta(days=7),  # Chạy hàng tuần
    catchup=False
)


def load_data_from_db():
    """
    Tải dữ liệu từ database thay vì từ file CSV
    """
    import psycopg2

    # Kết nối đến PostgreSQL
    conn = psycopg2.connect(
        host="postgres",
        database="ptpm",
        user="airflow",
        password="airflow",
        port=5432
    )

    # Tải bảng anime
    anime_df = pd.read_sql("SELECT * FROM anime", conn)

    # Tải bảng anime_with_synopsis
    synopsis_df = pd.read_sql("SELECT * FROM anime_with_synopsis", conn)

    # Tải bảng rating_complete
    rating_df = pd.read_sql("SELECT * FROM rating_complete", conn)

    # Đóng kết nối
    conn.close()

    # Chuyển đổi tên cột MAL_ID trong synopsis_df thành chữ thường để khớp với mal_id trong anime_df
    if 'MAL_ID' in synopsis_df.columns:
        synopsis_df = synopsis_df.rename(columns={'MAL_ID': 'mal_id'})

    # Đảm bảo mal_id là kiểu int trong cả hai DataFrame
    anime_df['mal_id'] = anime_df['mal_id'].astype(int)
    synopsis_df['mal_id'] = synopsis_df['mal_id'].astype(int)

    # Đảm bảo anime_id và user_id trong rating_df là kiểu int
    rating_df['anime_id'] = rating_df['anime_id'].astype(int)
    rating_df['user_id'] = rating_df['user_id'].astype(int)

    return anime_df, synopsis_df, rating_df


def preprocess_data(anime_df, synopsis_df):
    """
    Tiền xử lý dữ liệu
    """
    # Merge anime với synopsis
    anime_df = anime_df.merge(synopsis_df[['mal_id', 'sypnopsis']], on="mal_id", how='left')

    # Tiền xử lý text
    def preprocess_text(text):
        return str(text).lower().strip()

    anime_df['genres'] = anime_df['genres'].fillna('').apply(preprocess_text)
    anime_df['producers'] = anime_df['producers'].fillna('').apply(preprocess_text)
    anime_df['studios'] = anime_df['studios'].fillna('').apply(preprocess_text)
    anime_df['english_name'] = anime_df['english_name'].fillna('').apply(preprocess_text)
    # Đảm bảo sypnopsis là list of str
    anime_df['sypnopsis'] = anime_df['sypnopsis'].fillna('').apply(lambda x: str(x).split())

    return anime_df


def extract_features(anime_df):
    """
    Trích xuất các đặc trưng từ dữ liệu
    """
    # Tạo TF-IDF cho Genres, Producers, Studios, English Name
    tfidf = TfidfVectorizer(stop_words='english')

    tfidf_genres = tfidf.fit_transform(anime_df['genres'])
    tfidf_producers = tfidf.fit_transform(anime_df['producers'])
    tfidf_studios = tfidf.fit_transform(anime_df['studios'])
    tfidf_titles = tfidf.fit_transform(anime_df['english_name'])

    # Word2Vec cho synopsis
    word2vec_model = Word2Vec(sentences=anime_df['sypnopsis'], vector_size=100, window=5, min_count=1, workers=4)

    def get_w2v_vector(words, model, vector_size):
        vectors = [model.wv[word] for word in words if word in model.wv]
        return np.mean(vectors, axis=0) if vectors else np.zeros(vector_size)

    w2v_synopsis = np.array([get_w2v_vector(words, word2vec_model, 100) for words in anime_df['sypnopsis']])

    # Áp dụng trọng số cho các đặc trưng
    weight_genres = 0.4
    weight_titles = 0.1
    weight_studios = 0.05
    weight_producers = 0.05
    weight_synopsis = 0.4

    combined_features = np.hstack([
        weight_genres * tfidf_genres.toarray(),
        weight_producers * tfidf_producers.toarray(),
        weight_studios * tfidf_studios.toarray(),
        weight_titles * tfidf_titles.toarray(),
        weight_synopsis * w2v_synopsis
    ])

    return combined_features


def compute_bayesian_rating(rating_df, min_votes_percentile=0.75):
    """
    Tính Bayesian Average Rating (WR)
    """
    anime_stats = rating_df.groupby("anime_id")["rating"].agg(['mean', 'count']).reset_index()
    anime_stats.columns = ['anime_id', 'R', 'v']

    C = rating_df["rating"].mean()
    m = anime_stats["v"].quantile(min_votes_percentile)

    anime_stats["WR"] = (anime_stats["v"] / (anime_stats["v"] + m) * anime_stats["R"]) + (
            m / (anime_stats["v"] + m) * C)

    return anime_stats


def build_knn_model(combined_features):
    """
    Xây dựng mô hình KNN
    """
    nn_model = NearestNeighbors(n_neighbors=11, metric="cosine")
    nn_model.fit(combined_features)
    return nn_model


def train_model(**context):
    """
    Huấn luyện mô hình recommendation
    """
    setup_mlflow(tracking_uri=MLFLOW_TRACKING_URI, experiment_name=MLFLOW_EXPERIMENT_NAME)

    # Start MLflow run
    with mlflow.start_run(run_name="anime_recommendation_model") as run:
        # Ghi lại phiên bản của các thư viện quan trọng
        mlflow.log_param("sklearn_version", sklearn.__version__)
        mlflow.log_param("gensim_version", gensim.__version__)
        mlflow.log_param("cloudpickle_version", cloudpickle.__version__)
        mlflow.log_param("pandas_version", pd.__version__)
        mlflow.log_param("numpy_version", np.__version__)

        # Tải dữ liệu từ database
        anime_df, synopsis_df, rating_df = load_data_from_db()

        # Tiền xử lý dữ liệu
        anime_df = preprocess_data(anime_df, synopsis_df)

        # Trích xuất đặc trưng
        combined_features = extract_features(anime_df)

        # Tính Bayesian Rating
        anime_ratings = compute_bayesian_rating(rating_df)

        # Xây dựng KNN model
        nn_model = build_knn_model(combined_features)

        # Lưu index mapping anime_id -> index
        anime_index = {int(anime_id): idx for idx, anime_id in enumerate(anime_df['mal_id'])}

        # Lưu các thành phần cần thiết vào MLflow
        mlflow.log_param("vector_size", 100)
        mlflow.log_param("min_votes_percentile", 0.75)

        # Lưu một bản sao cần thiết của anime_df để giảm kích thước model
        anime_df_slim = anime_df[['mal_id', 'name', 'genres', 'producers', 'studios', 'score']].copy()

        # Đảm bảo kiểu dữ liệu
        anime_df_slim['mal_id'] = anime_df_slim['mal_id'].astype(int)
        anime_df_slim['name'] = anime_df_slim['name'].astype(str)
        anime_df_slim['genres'] = anime_df_slim['genres'].astype(str)
        anime_df_slim['producers'] = anime_df_slim['producers'].astype(str)
        anime_df_slim['studios'] = anime_df_slim['studios'].astype(str)
        anime_df_slim['score'] = anime_df_slim['score'].astype(float)

        # Đóng gói mô hình để serve
        class AnimeRecommendationModelSimplified(mlflow.pyfunc.PythonModel):
            def __init__(self, nn_model, anime_df, anime_index, anime_ratings, combined_features):
                self.nn_model = nn_model
                self.anime_df = anime_df
                self.anime_index = anime_index
                self.anime_ratings = anime_ratings
                self.combined_features = combined_features

            def predict(self, context, model_input):
                """
                Model input: {"anime_id": int, "top_n": int, "max_per_rank": int}
                """
                try:
                    # Đảm bảo kiểu dữ liệu của input
                    anime_id = int(model_input.get("anime_id", 0))
                    top_n = int(model_input.get("top_n", 10))
                    max_per_rank = int(model_input.get("max_per_rank", 3))

                    if anime_id not in self.anime_index:
                        return {"error": "Anime ID not found"}

                    idx = self.anime_index[anime_id]
                    distances, indices = self.nn_model.kneighbors([self.combined_features[idx]],
                                                                  n_neighbors=min(top_n + 10, len(self.anime_df)))

                    similar_anime = []
                    rank_count = {}

                    for j, i in enumerate(indices[0][1:]):  # Bỏ phần tử đầu tiên (chính nó)
                        similarity_score = float(round(1 - distances[0][j + 1], 4))
                        anime_info = self.anime_df.iloc[i]

                        # Lấy rating Bayesian WR
                        anime_wr = self.anime_ratings[self.anime_ratings["anime_id"] == anime_info["mal_id"]]["WR"]
                        anime_rating = float(round(anime_wr.values[0], 2)) if not anime_wr.empty else 0.0

                        # Giới hạn số anime có cùng mức độ tương đồng
                        if similarity_score in rank_count:
                            if rank_count[similarity_score] >= max_per_rank:
                                continue
                            rank_count[similarity_score] += 1
                        else:
                            rank_count[similarity_score] = 1

                        similar_anime.append({
                            "anime_id": int(anime_info["mal_id"]),
                            "title": str(anime_info["name"]),
                            "genres": str(anime_info["genres"]),
                            "producers": str(anime_info["producers"]),
                            "studios": str(anime_info["studios"]),
                            "similarity_score": float(similarity_score),
                            "rating": float(anime_rating)
                        })

                    # Sắp xếp
                    similar_anime = sorted(similar_anime, key=lambda x: (-x["similarity_score"], -x["rating"]))

                    return {"anime_id": int(anime_id), "similar_anime": similar_anime[:top_n]}
                except Exception as e:
                    return {"error": f"Prediction error: {str(e)}"}

        # Khởi tạo model
        recommendation_model = AnimeRecommendationModelSimplified(
            nn_model=nn_model,
            anime_df=anime_df_slim,
            anime_index=anime_index,
            anime_ratings=anime_ratings,
            combined_features=combined_features
        )

        # Log model
        mlflow.pyfunc.log_model(
            artifact_path="anime_similar_model",
            python_model=recommendation_model,
            registered_model_name="AnimeRecommendationModel"
        )

        # Lưu run_id để tác vụ tiếp theo dùng
        context['ti'].xcom_push(key='model_run_id', value=run.info.run_id)

        print(f"Đã huấn luyện mô hình thành công. Run ID: {run.info.run_id}")


def update_api_model(**context):
    """
    Cập nhật model mới trên FastAPI service
    """
    # Lấy run_id từ task trước
    run_id = context['ti'].xcom_pull(key='model_run_id')

    success_count = 0
    error_messages = []

    # URL của FastAPI service để cập nhật model
    for api_url in API_SERVERS:
        reload_url = f"{api_url}/reload"
        try:
            # Gọi API để cập nhật model
            response = requests.post(
                reload_url,
                json={
                    "model_name": "AnimeRecommendationModel",
                    "model_type": "1",  # Gửi dưới dạng chuỗi để tránh vấn đề type conversion
                    "source": "airflow",
                    "timestamp": datetime.now().isoformat()
                },
                timeout=300  # Timeout dài hơn cho việc tải model lớn
            )

            if response.status_code == 200:
                print(f"Đã cập nhật model thành công trên {api_url}. Phản hồi: {response.json()}")
                success_count += 1
            else:
                error_message = f"Không thể cập nhật model trên {api_url}. Mã trạng thái: {response.status_code}, Phản hồi: {response.text}"
                print(error_message)
                error_messages.append(error_message)
        except Exception as e:
            error_message = f"Lỗi khi gọi API {api_url}/reload: {str(e)}"
            print(error_message)
            error_messages.append(error_message)

    # Nếu không cập nhật được model trên bất kỳ server nào, báo lỗi
    if success_count == 0:
        raise Exception(f"Không thể cập nhật model trên bất kỳ API server nào. Lỗi: {', '.join(error_messages)}")
    elif success_count < len(API_SERVERS):
        print(f"Cảnh báo: Chỉ cập nhật thành công trên {success_count}/{len(API_SERVERS)} server")


# Định nghĩa các task
train_model_task = PythonOperator(
    task_id='train_recommendation_model',
    python_callable=train_model,
    provide_context=True,
    dag=dag,
)

update_api_model_task = PythonOperator(
    task_id='update_api_model',
    python_callable=update_api_model,
    provide_context=True,
    dag=dag,
)

# Thiết lập dependencies
train_model_task >> update_api_model_task