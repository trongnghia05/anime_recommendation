import os
import json
import pandas as pd
import psycopg2
import mlflow
import mlflow.pyfunc
import mlflow.spark
import logging
from datetime import datetime

from mlflow.tracking import MlflowClient
from elasticsearch import Elasticsearch
from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://airflow:airflow@postgres:5432/ptpm")
MODEL_INFO_FILE = os.getenv("MODEL_INFO_FILE", "/tmp/model_info.json")

# Initialize FastAPI
app = FastAPI(
    title="Anime Recommendation API",
    description="API for anime recommendations and search",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Elasticsearch and PostgreSQL connections
es = Elasticsearch("http://elasticsearch:9200")
pg_conn = psycopg2.connect(DATABASE_URL)

# Constants
HTTPS_STATUS_CODES = {
    "BAD_REQUEST": 400,
    "NOT_FOUND": 404,
    "SERVER_INTERNAL_ERROR": 500,
}

# Global variables for models
model_home = None
model_similar = None


# Models for request/response validation
class AnimeItem(BaseModel):
    anime_id: int
    title: str
    genres: str
    producers: str
    studios: str
    similarity_score: float
    rating: float


class SimilarAnimeResponse(BaseModel):
    anime_id: int
    similar_anime: List[AnimeItem]


class ModelInfo(BaseModel):
    model_name: str
    model_type: int  # 0: home, 1: similar
    model_uri: str
    version: str
    timestamp: datetime


# Quản lý thông tin model
class ModelManager:
    def __init__(self, model_info_file=MODEL_INFO_FILE):
        self.model_info_file = model_info_file
        self.model_info = self._load_model_info()

    def _load_model_info(self) -> Dict[str, Any]:
        """Tải thông tin model gần nhất từ file JSON"""
        try:
            if os.path.exists(self.model_info_file):
                with open(self.model_info_file, 'r') as f:
                    model_info = json.load(f)
                logger.info(f"Loaded model info: {model_info}")
                return model_info
            else:
                logger.info(f"Model info file not found at {self.model_info_file}. Creating new.")
                return {"models": {}}
        except Exception as e:
            logger.error(f"Error loading model info: {str(e)}")
            return {"models": {}}

    def save_model_info(self, model_type: int, model_name: str, model_uri: str, version: str):
        """Lưu thông tin model mới"""
        if "models" not in self.model_info:
            self.model_info["models"] = {}

        # Chuyển đổi model_type thành string key
        type_key = "home" if model_type == 0 else "similar"

        # Lưu thông tin model
        self.model_info["models"][type_key] = {
            "model_name": model_name,
            "model_type": model_type,
            "model_uri": model_uri,
            "version": version,
            "timestamp": datetime.now().isoformat()
        }

        # Ghi ra file
        try:
            with open(self.model_info_file, 'w') as f:
                json.dump(self.model_info, f, indent=4)
            logger.info(f"Saved model info to {self.model_info_file}")
        except Exception as e:
            logger.error(f"Error saving model info: {str(e)}")

    def get_latest_model(self, model_type: int) -> Optional[Dict[str, Any]]:
        """Lấy thông tin model gần nhất theo loại"""
        type_key = "home" if model_type == 0 else "similar"

        if "models" in self.model_info and type_key in self.model_info["models"]:
            return self.model_info["models"][type_key]

        return None


# Khởi tạo Model Manager
model_manager = ModelManager()


def get_popular_anime():
    """Lấy danh sách anime người dùng đang xem dở"""
    with pg_conn.cursor() as cur:
        sql = """
            SELECT
                anime_with_synopsis."MAL_ID" as id,
                anime_with_synopsis."Name" as name,
                anime.popularity
            FROM
                animelist
            INNER JOIN
                anime
                ON animelist.anime_id = anime.mal_id
            INNER JOIN
                anime_with_synopsis
                ON anime_with_synopsis."MAL_ID" = animelist.id
            ORDER BY anime.popularity DESC
            LIMIT 10;
        """
        cur.execute(sql)
        animes = cur.fetchall()

        if not animes:
            raise HTTPException(
                status_code=404,
                detail="No anime found for this user."
            )

        result = []
        for anime in animes:
            result.append({
                "anime_id": anime[0],
                "name": anime[1],
                "popularity": anime[2]
            })

        return result


# --------------------------------------------------
# Model Management
# --------------------------------------------------
def load_model_from_mlflow(model_name: str, model_version: str):
    """Tải model từ MLflow registry"""
    try:
        # Thiết lập thông tin xác thực S3/MinIO
        os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'
        os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://minio:9000'

        # Kết nối tới MLflow
        mlflow.set_tracking_uri("http://mlflow:5000")

        # Tạo URI model
        model_uri = f"models:/{model_name}/{model_version}"

        # Tải model
        return mlflow.pyfunc.load_model(model_uri), model_uri
    except Exception as e:
        logger.error(f"Error loading model from MLflow: {str(e)}")
        return None, None


def load_latest_models_on_startup():
    """Tải các model gần nhất khi khởi động"""
    global model_home, model_similar

    try:
        # Tải model home
        home_model_info = model_manager.get_latest_model(0)
        if home_model_info:
            logger.info(f"Loading home model: {home_model_info['model_name']} v{home_model_info['version']}")
            model, _ = load_model_from_mlflow(home_model_info['model_name'], home_model_info['version'])
            if model:
                model_home = model
                logger.info("Home model loaded successfully")
            else:
                logger.warning("Failed to load home model")

        # Tải model similar
        similar_model_info = model_manager.get_latest_model(1)
        if similar_model_info:
            logger.info(f"Loading similar model: {similar_model_info['model_name']} v{similar_model_info['version']}")
            model, _ = load_model_from_mlflow(similar_model_info['model_name'], similar_model_info['version'])
            if model:
                model_similar = model
                logger.info("Similar model loaded successfully")
            else:
                logger.warning("Failed to load similar model")

    except Exception as e:
        logger.error(f"Error loading models on startup: {str(e)}")


# Tải models khi khởi động
@app.on_event("startup")
def startup_event():
    load_latest_models_on_startup()


@app.post("/reload", tags=["Model Management"])
def reload_model(data: dict = Body(...)):
    """Tải lại model từ MLflow registry"""
    try:
        model_name = data.get("model_name")
        model_type = data.get("model_type")

        if not model_name:
            raise HTTPException(status_code=400, detail="model_name is required")

        # Thiết lập thông tin xác thực S3/MinIO
        os.environ['AWS_ACCESS_KEY_ID'] = 'minioadmin'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'minioadmin'
        os.environ['MLFLOW_S3_ENDPOINT_URL'] = 'http://minio:9000'

        # Kết nối tới MLflow
        mlflow.set_tracking_uri("http://mlflow:5000")
        client = MlflowClient()

        # Lấy phiên bản mới nhất
        latest_versions = client.get_latest_versions(model_name, stages=["Production", "None"])
        if not latest_versions:
            raise HTTPException(status_code=404, detail=f"No versions found for model {model_name}")

        model_version = latest_versions[0]

        # Tải model và lưu vào biến toàn cục
        model_uri = f"models:/{model_name}/{model_version.version}"
        logger.info(f"Loading model: {model_name} v{model_version.version}")
        logger.info(f"Model URI: {model_uri}")
        logger.info(f"Model Type: {model_type}")

        loaded_model = mlflow.pyfunc.load_model(model_uri)

        if model_type == 0:
            global model_home
            model_home = loaded_model
        else:
            global model_similar
            model_similar = loaded_model

        # Lưu metadata cho model
        model_manager.save_model_info(
            model_type=model_type,
            model_name=model_name,
            model_uri=model_uri,
            version=model_version.version
        )

        # Tương thích ngược - lưu metadata để /metadata endpoint có thể truy cập
        with open("/tmp/model_metadata.json", "w") as f:
            json.dump({
                "model_name": model_name,
                "version": model_version.version,
                "timestamp": data.get("timestamp", datetime.now().isoformat())
            }, f)

        return {
            "success": True,
            "message": f"Model loaded: {model_name} v{model_version.version}"
        }

    except Exception as e:
        logger.error(f"Error reloading model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metadata", tags=["Model Management"])
def get_model_metadata():
    """Lấy thông tin về model hiện tại"""
    try:
        # Ưu tiên lấy thông tin từ file tương thích cũ
        if os.path.exists("/tmp/model_metadata.json"):
            with open("/tmp/model_metadata.json", "r") as f:
                metadata = json.load(f)
            return metadata

        # Nếu không có, lấy từ model_manager
        models_info = {
            "home": model_manager.get_latest_model(0),
            "similar": model_manager.get_latest_model(1)
        }

        if not models_info["home"] and not models_info["similar"]:
            return {"status": "No models loaded"}

        return models_info

    except Exception as e:
        raise HTTPException(
            status_code=HTTPS_STATUS_CODES["SERVER_INTERNAL_ERROR"],
            detail=str(e),
        )


@app.get("/models/info", tags=["Model Management"])
def get_all_models_info():
    """Lấy thông tin về tất cả các model đã lưu"""
    return model_manager.model_info


# --------------------------------------------------
# Search
# --------------------------------------------------
@app.get("/search/suggestions", tags=["Search"])
def search_anime_suggestions(
        q: str = Query(..., description="Search query"),
        limit: int = Query(5, description="Maximum number of suggestions")
):
    """Tìm kiếm gợi ý anime theo tên"""
    search_term = q.strip()
    query = {
        "size": limit,
        "query": {
            "bool": {
                "should": [
                    {"prefix": {"Name.keyword": {"value": search_term, "boost": 10.0, "case_insensitive": True}}},
                    {"wildcard": {
                        "Name.keyword": {"value": f"*{search_term}*", "boost": 1.0, "case_insensitive": True}}},
                    {"match_phrase_prefix": {
                        "Name": {
                            "query": search_term,
                            "boost": 5.0
                        }
                    }}
                ]
            }
        },
        "_source": ["MAL_ID", "Name", "Genres"],
        "sort": [
            "_score",
            {"Name.keyword": {"order": "asc"}}
        ]
    }

    try:
        es_result = es.search(index="anime_with_synopsis_index", body=query)
        suggestions = [hit["_source"] for hit in es_result["hits"]["hits"]]
        print(suggestions)
    except Exception as e:
        print(e)
        return {"suggestions": []}

    return {"suggestions": suggestions}


# --------------------------------------------------
# User
# --------------------------------------------------
@app.get("/users/{user_id}", tags=["Users"])
def get_user(user_id: int):
    """Lấy thông tin người dùng theo ID"""
    with pg_conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()

        if user:
            return {"user_id": user[0], "name": user[1], "email": user[2]}
        else:
            raise HTTPException(
                status_code=HTTPS_STATUS_CODES["NOT_FOUND"],
                detail="User not found",
            )


@app.get("/user/{user_id}", tags=["Users"], include_in_schema=False)
def get_user_info(user_id: int):
    """Legacy endpoint: Lấy thông tin người dùng theo ID"""
    return get_user(user_id)


# --------------------------------------------------
# Anime
# --------------------------------------------------
@app.get("/animes/{anime_id}", tags=["Anime"])
def get_anime(anime_id: int):
    """Lấy thông tin chi tiết về anime theo ID"""
    with pg_conn.cursor() as cur:
        sql = """
            SELECT 
                "MAL_ID" AS id, 
                "Name" AS name, 
                "sypnopsis" AS description, 
                "Genres" AS genres,
                "Score" as rating
            FROM anime_with_synopsis 
            WHERE "MAL_ID" = %s;
        """
        cur.execute(sql, (anime_id,))
        anime = cur.fetchone()

        if anime:
            return {
                "id": anime[0],
                "title": anime[1],
                "description": anime[2],
                "genres": anime[3].strip().split(","),
                "rating": anime[4]
            }
        else:
            raise HTTPException(
                status_code=HTTPS_STATUS_CODES["NOT_FOUND"],
                detail="Anime not found",
            )


@app.get("/anime/{anime_id}", tags=["Anime"], include_in_schema=False)
def get_anime_info(anime_id: int):
    """Legacy endpoint: Lấy thông tin chi tiết về anime theo ID"""
    return get_anime(anime_id)


# --------------------------------------------------
# Recommendations
# --------------------------------------------------
@app.get("/recommendations/user/{user_id}", tags=["Recommendations"])
def get_recommendations_for_user(user_id: int, limit: int = 10):
    """Đề xuất anime cho người dùng dựa trên lịch sử xem"""
    global model_home

    if model_home is None:
        # Nếu model chưa được tải, thử tải model gần nhất
        latest_model_info = model_manager.get_latest_model(0)
        if latest_model_info:
            logger.info(
                f"Trying to load latest home model: {latest_model_info['model_name']} v{latest_model_info['version']}")
            model, _ = load_model_from_mlflow(latest_model_info['model_name'], latest_model_info['version'])
            if model:
                model_home = model
            else:
                raise HTTPException(
                    status_code=HTTPS_STATUS_CODES["SERVER_INTERNAL_ERROR"],
                    detail="Failed to load home model. Please call /reload first."
                )
        else:
            raise HTTPException(
                status_code=HTTPS_STATUS_CODES["SERVER_INTERNAL_ERROR"],
                detail="Model not loaded. Call /reload first."
            )

    try:
        input_data = pd.DataFrame([{
            'user_id': user_id,
            'top_n': limit
        }])

        # Gọi predict với DataFrame
        recommendations = model_home.predict(input_data)

        # recommendations là list của list, lấy phần tử đầu tiên
        if recommendations and len(recommendations) > 0:
            if recommendations[0][0]["explanation"] == "Đề xuất dựa trên các yếu tố khác":
                return {
                    "user_id": user_id,
                    "recommendations": get_popular_anime()
                }
            else:
                return {
                    "user_id": user_id,
                    "recommendations": recommendations[0]
                }
        else:
            return {
                "user_id": user_id,
                "recommendations": []
            }
    except Exception as e:
        raise HTTPException(
            status_code=HTTPS_STATUS_CODES["SERVER_INTERNAL_ERROR"],
            detail=str(e)
        )


@app.get("/recommend/because_you_watch/{user_id}", tags=["Recommendations"], include_in_schema=False)
def recommend_anime(user_id: int, limit: int = 10):
    """Legacy endpoint: Đề xuất anime cho người dùng"""
    return get_recommendations_for_user(user_id, limit)


@app.get("/recommendations/similar/{anime_id}", tags=["Recommendations"], response_model=SimilarAnimeResponse)
def get_similar_animes(
        anime_id: int,
        top_n: int = Query(10, description="Số lượng anime tương tự muốn lấy"),
        max_per_rank: int = Query(3, description="Số lượng tối đa anime cho mỗi mức độ tương đồng")
):
    """Lấy danh sách anime tương tự với anime được chỉ định"""
    global model_similar

    if model_similar is None:
        # Nếu model chưa được tải, thử tải model gần nhất
        latest_model_info = model_manager.get_latest_model(1)
        if latest_model_info:
            logger.info(
                f"Trying to load latest similar model: {latest_model_info['model_name']} v{latest_model_info['version']}")
            model, _ = load_model_from_mlflow(latest_model_info['model_name'], latest_model_info['version'])
            if model:
                model_similar = model
            else:
                raise HTTPException(status_code=503,
                                    detail="Không thể tải mô hình tương tự. Vui lòng tải mô hình trước.")
        else:
            raise HTTPException(status_code=503, detail="Mô hình chưa được tải. Vui lòng tải mô hình trước.")

    try:
        result = model_similar.predict({
            "anime_id": anime_id,
            "top_n": top_n,
            "max_per_rank": max_per_rank
        })

        if isinstance(result, dict) and "error" in result:
            if "Anime ID not found" in result["error"]:
                raise HTTPException(status_code=404, detail=f"Không tìm thấy anime có ID {anime_id}")
            else:
                raise HTTPException(status_code=500, detail=result["error"])

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi dự đoán: {str(e)}")


@app.get("/recommend/similar/{anime_id}", tags=["Recommendations"], include_in_schema=False)
def get_similar_anime(
        anime_id: int,
        top_n: int = Query(10, description="Số lượng anime tương tự muốn lấy"),
        max_per_rank: int = Query(3, description="Số lượng tối đa anime cho mỗi mức độ tương đồng")
):
    """Legacy endpoint: Lấy danh sách anime tương tự"""
    return get_similar_animes(anime_id, top_n, max_per_rank)


@app.get("/recommendations/continue-watching/{user_id}", tags=["Recommendations"])
def get_continue_watching_recommendations(user_id: int):
    """Lấy danh sách anime người dùng đang xem dở"""
    with pg_conn.cursor() as cur:
        sql = """
        SELECT 
            anime_with_synopsis."MAL_ID" as id, 
            anime_with_synopsis."Name" as name, 
            animelist.watched_episodes
        FROM 
            animelist
        INNER JOIN 
            anime 
            ON animelist.anime_id = anime.mal_id
        INNER JOIN 
            anime_with_synopsis 
            ON anime_with_synopsis."MAL_ID" = animelist.id
        WHERE 
            animelist.user_id = %s 
            AND animelist.watching_status = 1
        LIMIT 5;
        """
        cur.execute(sql, (user_id,))
        animes = cur.fetchall()

        if not animes:
            raise HTTPException(
                status_code=404,
                detail="No anime found for this user."
            )

        result = []
        for anime in animes:
            result.append({
                "id": anime[0],
                "title": anime[1],
                "episodeNumber": anime[2]
            })

        return {"user_id": user_id, "continue_watching": result}


@app.get("/recommend/continue_watching/{user_id}", tags=["Recommendations"], include_in_schema=False)
def get_continue_watching(user_id: int):
    """Legacy endpoint: Lấy danh sách anime người dùng đang xem dở"""
    return get_continue_watching_recommendations(user_id)


@app.get("/recommendations/trending/{user_id}", tags=["Recommendations"])
def get_trending_recommendations(user_id: int):
    """Lấy danh sách anime đang thịnh hành"""
    with pg_conn.cursor() as cur:
        sql = """
            SELECT DISTINCT ON (anime.watching)
                anime_with_synopsis."MAL_ID" as id,
                anime_with_synopsis."Name" as name,
                anime.watching
            FROM
                animelist
            INNER JOIN
                anime
                ON animelist.anime_id = anime.mal_id
            INNER JOIN
                anime_with_synopsis
                ON anime_with_synopsis."MAL_ID" = animelist.id
            ORDER BY anime.watching DESC, anime_with_synopsis."MAL_ID" ASC
            LIMIT 5;
        """
        cur.execute(sql)
        animes = cur.fetchall()

        if not animes:
            raise HTTPException(
                status_code=404,
                detail="No trending anime found."
            )

        result = []
        for anime in animes:
            result.append({
                "id": anime[0],
                "title": anime[1],
                "score": anime[2]
            })

        return {"user_id": user_id, "trending": result}


@app.get("/recommend/trending/{user_id}", tags=["Recommendations"], include_in_schema=False)
def get_trending(user_id: int):
    """Legacy endpoint: Lấy danh sách anime đang thịnh hành"""
    return get_trending_recommendations(user_id)


@app.get("/recommendations/top-rated/{user_id}", tags=["Recommendations"])
def get_top_rated_recommendations(user_id: int):
    """Lấy danh sách anime có đánh giá cao nhất"""
    with pg_conn.cursor() as cur:
        sql = """
            SELECT 
                a."MAL_ID" AS id,
                a."Name" AS title,
                anime.score AS rating
            FROM 
                anime
            INNER JOIN
                anime_with_synopsis a
                ON anime.mal_id = a."MAL_ID"
            ORDER BY 
                anime.score DESC
            LIMIT 5;
        """
        cur.execute(sql)
        animes = cur.fetchall()

        if not animes:
            raise HTTPException(
                status_code=404,
                detail="No top-rated anime found."
            )

        result = []
        for anime in animes:
            result.append({
                "id": anime[0],
                "title": anime[1],
                "rating": anime[2]
            })

        return {"user_id": user_id, "top_rate": result}




@app.get("/recommend/top_rate/{user_id}", tags=["Recommendations"], include_in_schema=False)
def get_top_rate(user_id: int):
    """Legacy endpoint: Lấy danh sách anime có đánh giá cao nhất"""
    return get_top_rated_recommendations(user_id)