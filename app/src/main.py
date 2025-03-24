import os
import psycopg2
from elasticsearch import Elasticsearch
from fastapi import FastAPI, HTTPException

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()

# Initialize Elasticsearch and PostgreSQL connections
es = Elasticsearch("http://elasticsearch:9200")
pg_conn = psycopg2.connect(DATABASE_URL)


HTTPS_STATUS_CODES = {
    "BAD_REQUEST": 400,
    "NOT_FOUND": 404,
    "SERVER_INTERNAL_ERROR": 500,
}


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
