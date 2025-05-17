import os
import boto3

# Set MinIO credentials
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin"
endpoint_url = "http://minio:9000"

# Create S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=endpoint_url,
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
)

# Create the bucket if it doesn't exist
bucket_name = "mlflow"
try:
    s3_client.head_bucket(Bucket=bucket_name)
    print(f"Bucket '{bucket_name}' already exists")
except Exception as e:
    print(f"Creating bucket '{bucket_name}'...")
    s3_client.create_bucket(Bucket=bucket_name)
    print(f"Bucket '{bucket_name}' created successfully")
