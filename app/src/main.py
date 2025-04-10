import os
import psycopg2
from elasticsearch import Elasticsearch
from fastapi import FastAPI, HTTPException, Body
import mlflow
from mlflow.tracking import MlflowClient
import json
from fastapi.middleware.cors import CORSMiddleware


DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],  # Cho phép tất cả các phương thức HTTP
    allow_headers=["*"],  # Cho phép tất cả các header
)
# Initialize Elasticsearch and PostgreSQL connections
es = Elasticsearch("http://elasticsearch:9200")
pg_conn = psycopg2.connect(DATABASE_URL)


HTTPS_STATUS_CODES = {
    "BAD_REQUEST": 400,
    "NOT_FOUND": 404,
    "SERVER_INTERNAL_ERROR": 500,
}

# Biến toàn cục để lưu model
model = None


@app.post("/reload")
def reload_model(data: dict = Body(...)):
    """Tải lại model từ MLflow registry"""
    global model

    try:
        model_name = data.get("model_name")
        if not model_name:
            raise HTTPException(status_code=400, detail="model_name is required")

        # Thiết lập thông tin xác thực S3/MinIO - Quan trọng để load model từ MinIO
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
        print("model_uri:", model_uri)
        model = mlflow.pyfunc.load_model(model_uri)

        # Lưu metadata để /metadata endpoint có thể truy cập
        with open("/tmp/model_metadata.json", "w") as f:
            json.dump({
                "model_name": model_name,
                "version": model_version.version,
                "timestamp": data.get("timestamp", "")
            }, f)

        return {"success": True, "message": f"Model loaded: {model_name} v{model_version.version}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
def search_anime(name: str, limit: int = 5):
    query = {
        "size": limit,
        "query": {"wildcard": {"name.keyword": f"*{name.lower()}*"}},
    }
    results = None
    try:
        es_result = es.search(index="anime", body=query)
        results = [
            {
                "animeId": hit["_source"]["animeId"],
                "name": hit["_source"].get("name", "Unknown"),
                "rating": hit["_source"].get("rating", "N/A"),
                "scores": hit["_source"].get("scores", "N/A"),
                "genres": hit["_source"].get("genres", "N/A"),
                "type": hit["_source"].get("type", "N/A"),
                "episodes": hit["_source"].get("episodes", "N/A"),
                "studio": hit["_source"].get("studio", "N/A"),
                "source": hit["_source"].get("source", "N/A"),
                "ranking": hit["_source"].get("ranking", "N/A"),
            }
            for hit in es_result["hits"]["hits"]
        ]
    except Exception as e:
        raise HTTPException(
            status_code=HTTPS_STATUS_CODES["SERVER_INTERNAL_ERROR"],
            detail=str(e),
        )

    if results is None or len(results) == 0:
        raise HTTPException(status_code=HTTPS_STATUS_CODES["NOT_FOUND"])

    return {"results": results}


@app.get("/user/{user_id}")
def get_user_info(user_id: int):
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


@app.get("/recommend/{user_id}")
def recommend_anime(user_id: int, limit: int = 10):
    """Đề xuất anime cho người dùng"""
    global model

    if model is None:
        raise HTTPException(
            status_code=HTTPS_STATUS_CODES["SERVER_INTERNAL_ERROR"],
            detail="Model not loaded. Call /reload first."
        )

    try:
        # Tạo DataFrame với đúng định dạng mà model mong đợi
        import pandas as pd
        input_data = pd.DataFrame([{
            'user_id': user_id,
            'top_n': limit
        }])

        # Gọi predict với DataFrame
        recommendations = model.predict(input_data)

        # recommendations là list của list, lấy phần tử đầu tiên
        if recommendations and len(recommendations) > 0:
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

@app.get("/metadata")
def get_model_metadata():
    try:
        with open("/tmp/model_metadata.json", "r") as f:
            metadata = f.read()
        return metadata
    except Exception as e:
        raise HTTPException(
            status_code=HTTPS_STATUS_CODES["SERVER_INTERNAL_ERROR"],
            detail=str(e),
        )
