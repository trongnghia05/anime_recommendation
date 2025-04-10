from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.http.operators.http import SimpleHttpOperator
import pandas as pd
import numpy as np
import os
import sys
import json
import requests
import logging
import mlflow

# Thêm đường dẫn cho các module
sys.path.append('/opt/airflow')

# Import các module cần thiết
from src.model.recommender import ContentBase
from src.mlflow_utils import setup_mlflow, log_model_to_mlflow, evaluate_and_log_metrics

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MLflow settings
MLFLOW_TRACKING_URI = os.environ.get('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
MLFLOW_EXPERIMENT_NAME = os.environ.get('MLFLOW_EXPERIMENT_NAME', 'anime_recommendation_system')
REGISTERED_MODEL_NAME = os.environ.get('REGISTERED_MODEL_NAME', 'anime_recommender')

# API settings
API_SERVERS = json.loads(os.environ.get('API_SERVERS', '["http://fastapi:8000"]'))



# Đối số mặc định cho DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

import psycopg2

conn = psycopg2.connect(
    host="postgres",
    database="airflow",
    user="airflow",
    password="airflow",
    port=5432
)

# Định nghĩa DAG
dag = DAG(
    'anime_recommendation_system',
    default_args=default_args,
    description='DAG cho hệ thống đề xuất anime với MLflow',
    schedule_interval='0 0 * * *',  # Chạy hàng ngày vào lúc 00:00
    catchup=False,
)

# Định nghĩa các thư mục
DATA_DIR = '/opt/airflow/data'
CACHE_DIR = '/opt/airflow/cache'

# Tạo thư mục nếu chưa tồn tại
for directory in [DATA_DIR, CACHE_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)


# Định nghĩa các hàm cho các task
def extract_anime_data(**kwargs):
    """Trích xuất dữ liệu anime từ nguồn và lưu vào CSV"""
    # Phương án 1: Đọc từ database
    try:

        # Truy vấn dữ liệu anime
        anime_data = pd.read_sql("SELECT * FROM anime", conn)
        conn.close()

        # Lưu vào CSV
        anime_path = os.path.join(DATA_DIR, 'anime.csv')
        anime_data.to_csv(anime_path, index=False)
        logger.info(f"Đã trích xuất thành công {len(anime_data)} bản ghi anime")
        return anime_path

    except Exception as e:
        logger.warning(f"Không thể trích xuất từ database: {e}")

        # Phương án 2: Sử dụng file CSV hiện có
        anime_path = os.path.join(DATA_DIR, 'anime.csv')
        if os.path.exists(anime_path):
            logger.info(f"Sử dụng file CSV anime hiện có: {anime_path}")
            return anime_path
        else:
            raise Exception("Không có dữ liệu anime khả dụng")


def extract_user_data(**kwargs):
    """Trích xuất dữ liệu đánh giá của người dùng và lưu vào CSV"""
    # Phương án 1: Đọc từ database
    try:
        user_data = pd.read_sql("SELECT * FROM animelist", conn)

        # Lưu vào CSV
        user_path = os.path.join(DATA_DIR, 'animelist.csv')
        user_data.to_csv(user_path, index=False)
        logger.info(f"Đã trích xuất thành công {len(user_data)} đánh giá của người dùng")
        return user_path

    except Exception as e:
        logger.warning(f"Không thể trích xuất từ database: {e}")

        # Phương án 2: Sử dụng file CSV hiện có
        user_path = os.path.join(DATA_DIR, 'animelist.csv')
        if os.path.exists(user_path):
            logger.info(f"Sử dụng file CSV người dùng hiện có: {user_path}")
            return user_path
        else:
            raise Exception("Không có dữ liệu người dùng khả dụng")


def train_and_evaluate_model(**kwargs):
    """Huấn luyện và đánh giá model, log vào MLflow"""
    ti = kwargs['ti']
    anime_path = ti.xcom_pull(task_ids='extract_anime_data')
    user_path = ti.xcom_pull(task_ids='extract_user_data')

    # Thiết lập MLflow
    setup_mlflow(tracking_uri=MLFLOW_TRACKING_URI, experiment_name=MLFLOW_EXPERIMENT_NAME)

    # Khởi tạo recommender
    recommender = ContentBase(cache_dir=CACHE_DIR)

    # Tải dữ liệu tiền xử lý hoặc xử lý mới
    if not recommender.load_preprocessed_data():
        logger.info("Đang tiền xử lý dữ liệu anime...")
        recommender.preprocess_data(anime_path)

    # Xử lý dữ liệu người dùng
    user_data = pd.read_csv(user_path)
    recommender.process_user_data(user_data)

    # Xây dựng profile cho người dùng tích cực
    user_count = min(100, len(user_data['user_id'].unique()))
    top_users = user_data['user_id'].value_counts().head(user_count).index.tolist()
    logger.info(f"Đang xây dựng profile cho {len(top_users)} người dùng tích cực nhất")

    # Xây dựng profile cho mỗi người dùng
    for user_id in top_users:
        recommender.calculate_user_profile(user_id)
    mlflow.end_run()
    # Log model vào MLflow
    with mlflow.start_run(run_name=f"anime_recommender_{datetime.now().strftime('%Y%m%d_%H%M%S')}") as run:
        run_id = run.info.run_id

        # Log model vào MLflow
        log_model_to_mlflow(recommender, run_id=run_id, model_name=REGISTERED_MODEL_NAME)

        # Đánh giá model
        logger.info("Đang thực hiện đánh giá model...")
        evaluation_metrics = recommender.evaluate(
            test_size=0.2,
            k_values=[5, 10, 20],
            random_state=42,
            max_users=50  # Giới hạn số lượng người dùng để đánh giá nhanh hơn
        )

        # Log metrics vào run
        evaluate_and_log_metrics(recommender, evaluation_metrics, run_id=run_id)

        return {
            "run_id": run_id,
            "model_name": REGISTERED_MODEL_NAME,
            "evaluation_metrics": evaluation_metrics
        }


def notify_api_servers(**kwargs):
    """Thông báo cho tất cả API servers để tải lại model"""
    ti = kwargs['ti']
    model_result = ti.xcom_pull(task_ids='train_and_evaluate_model')

    if not model_result:
        logger.warning("Không có model mới được huấn luyện, bỏ qua thông báo API")
        return {
            "success": False,
            "reason": "Không có model mới được huấn luyện"
        }

    # Thông báo cho mỗi API server
    success_count = 0
    errors = []

    for api_url in API_SERVERS:
        reload_url = f"{api_url}/reload"
        try:
            # Gửi POST request đến endpoint /reload của API
            response = requests.post(
                reload_url,
                json={
                    "model_name": model_result["model_name"],
                    "source": "airflow",
                    "timestamp": datetime.now().isoformat()
                },
                timeout=30  # Timeout 30 giây
            )

            # Kiểm tra response
            if response.status_code == 200:
                logger.info(f"Đã thông báo thành công cho API server: {api_url}")
                success_count += 1
            else:
                error_msg = f"Lỗi khi thông báo cho API server {api_url}: {response.status_code} - {response.text}"
                logger.error(error_msg)
                errors.append(error_msg)

        except Exception as e:
            error_msg = f"Lỗi khi kết nối đến API server {api_url}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

    # Kiểm tra kết quả thông báo
    if success_count == 0 and len(API_SERVERS) > 0:
        logger.error("Không thể thông báo cho bất kỳ API server nào!")
        return {
            "success": False,
            "errors": errors
        }

    if success_count < len(API_SERVERS):
        logger.warning(f"Chỉ thông báo thành công cho {success_count}/{len(API_SERVERS)} API servers")
    else:
        logger.info(f"Đã thông báo thành công cho tất cả {success_count} API servers")

    return {
        "success": True,
        "success_count": success_count,
        "total_servers": len(API_SERVERS),
        "errors": errors
    }


# Tạo các task
extract_anime_task = PythonOperator(
    task_id='extract_anime_data',
    python_callable=extract_anime_data,
    provide_context=True,
    dag=dag,
)

extract_user_task = PythonOperator(
    task_id='extract_user_data',
    python_callable=extract_user_data,
    provide_context=True,
    dag=dag,
)

train_evaluate_task = PythonOperator(
    task_id='train_and_evaluate_model',
    python_callable=train_and_evaluate_model,
    provide_context=True,
    dag=dag,
)

notify_api_task = PythonOperator(
    task_id='notify_api_servers',
    python_callable=notify_api_servers,
    provide_context=True,
    dag=dag,
)

# Định nghĩa phụ thuộc giữa các task
extract_anime_task >> train_evaluate_task
extract_user_task >> train_evaluate_task
train_evaluate_task >> notify_api_task