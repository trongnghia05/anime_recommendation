from datetime import datetime, timedelta
import os
import json
import mlflow
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash import BashOperator
from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import ParamGridBuilder, CrossValidator

# MLflow settings
MLFLOW_TRACKING_URI = os.environ.get('MLFLOW_TRACKING_URI', 'http://mlflow:5000')
MLFLOW_EXPERIMENT_NAME = 'als_anime_recommendation'
API_SERVERS = json.loads(os.environ.get('API_SERVERS', '["http://fastapi:8000"]'))

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    'als_anime_training',
    default_args=default_args,
    schedule_interval='@weekly',
    catchup=False
)

def train_als_model(**context):
    # Khởi tạo spark session
    spark = SparkSession.builder \
        .appName("ALSAnimeTraining") \
        .master("spark://spark-master:7077") \
        .getOrCreate()
    
    # Lấy data từ HDFS
    ratings = spark.read.csv("hdfs://namenode:9000/data/rating_complete.csv", header=True)
    
    # Chuẩn bị data
    train, test = ratings.randomSplit([0.8, 0.2], seed=42)
    
    # Khởi tạo model ALS
    als = ALS(
        userCol="user_id",
        itemCol="anime_id",
        ratingCol="rating",
        nonnegative=True,
        coldStartStrategy="drop"
    )
    
    # Build parameter grid
    param_grid = ParamGridBuilder() \
        .addGrid(als.rank, [10, 50, 100]) \
        .addGrid(als.regParam, [0.01, 0.1]) \
        .build()
    
    # Dùng RMSE để đánh giá model
    evaluator = RegressionEvaluator(
        metricName="rmse", 
        labelCol="rating",
        predictionCol="prediction"
    )
    
    # Cross validation
    cv = CrossValidator(
        estimator=als,
        estimatorParamMaps=param_grid,
        evaluator=evaluator,
        numFolds=3
    )
    
    # Train model
    model = cv.fit(train)
    best_model = model.bestModel
    
    # Log
    with mlflow.start_run(experiment_id=mlflow.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME).experiment_id):
        mlflow.spark.log_model(
            best_model,
            "als_anime_model",
            registered_model_name="als_anime_recommender"
        )
        mlflow.log_param("rank", best_model.rank)
        mlflow.log_param("regParam", best_model.regParam)
        mlflow.log_metric("rmse", evaluator.evaluate(best_model.transform(test)))

    # Lưu model lên HDFS
    best_model.save("hdfs://namenode:9000/model/als_anime_latest")

    spark.stop()

# Tạo task
train_task = PythonOperator(
    task_id='train_als_model',
    python_callable=train_als_model,
    dag=dag
)
