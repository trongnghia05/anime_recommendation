import os
import mlflow
import mlflow.spark
from pyspark.sql import SparkSession
from pyspark.ml.tuning import CrossValidatorModel

APP_NAME = "Upload"
spark = SparkSession.builder.appName(APP_NAME).getOrCreate()
model_path = "hdfs://172.18.0.2:9000/model/model_200_0.1"
cv_model = CrossValidatorModel.load(model_path)
best_model = cv_model.bestModel

mlflow.set_tracking_uri("http://mlflow:5000")
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://minio:9000"
mlflow.set_experiment("ALS-Recommendation")

with mlflow.start_run():
    mlflow.spark.log_model(
        spark_model=best_model,
        artifact_path="als_model",
        registered_model_name="ALS-Recommendation",
    )
