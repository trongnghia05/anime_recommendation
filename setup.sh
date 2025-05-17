#!/bin/bash

echo "Setting up Anime Recommendation System..."

# Create necessary directories
mkdir -p app/airflow/logs
mkdir -p app/mlflow/mlruns
mkdir -p app/data

# # Check if data files exist
# if [ ! -f "app/data/anime.csv" ] || [ ! -f "app/data/animelist.csv" ] || [ ! -f "app/data/rating_complete.csv" ]; then
#     echo "Error: Required data files not found in app/data directory!"
#     echo "Please ensure the following files exist:"
#     echo "- app/data/anime.csv"
#     echo "- app/data/animelist.csv"
#     echo "- app/data/rating_complete.csv"
#     exit 1
# fi

# Start the system
cd app && docker compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Copy source files to spark-master
echo "Copying source files to spark-master..."
docker cp src spark-master:/
docker cp libs/elasticsearch-hadoop-7.15.1.jar spark-master:elasticsearch-hadoop-7.15.1.jar

# Copy processed data to namenode
echo "Copying data files to namenode..."
docker cp ../data/movies/anime.csv namenode:/
docker cp ../data/movies/animelist.csv namenode:/
docker cp ../data/movies/anime_refined_modified.csv namenode:/
docker cp ../data/ratings/rating_complete.csv namenode:/
docker cp ../data/ratings/short_anime_ratings.csv namenode:/

# Initialize HDFS
echo "Initializing HDFS..."
docker exec -it namenode bash -c '
hdfs dfs -mkdir /data/
hdfs dfs -mkdir /model/
hdfs dfs -mkdir /result/
hdfs dfs -put short_anime_ratings.csv /data/
hdfs dfs -put rating_complete.csv /data/
hdfs dfs -put anime.csv /data/
hdfs dfs -put animelist.csv /data/
hdfs dfs -put anime_refined_modified.csv /data/
'

# Create directories in Spark master
echo "Creating directories in Spark master..."
docker exec -it spark-master bash -c '
mkdir -p /result/model/
mkdir -p /result/spark_nodes/
mkdir -p /result/read_file/
'

# Install required packages in Spark master
echo "Installing required packages in Spark master..."
docker exec -it spark-master bash -c '
python3 -m venv .venv
source .venv/bin/activate
apk update
apk add make automake gcc g++ subversion python3-dev nano
pip3 install numpy venv-pack
'

# Fix Python version issue in Spark worker
echo "Configuring Python version in Spark worker..."
docker exec -it spark-worker-a bash -c '
apk update
apk add nano
echo "export PYSPARK_PYTHON=/usr/local/bin/python3.7" >> spark/conf/spark-env.sh
echo "export PYSPARK_DRIVER_PYTHON=/usr/local/bin/python3.7" >> spark/conf/spark-env.sh
'

# # Initialize Airflow
# echo "Initializing Airflow..."
# docker exec -it airflow-webserver bash -c '
# airflow db init
# airflow users create \
#     --username admin \
#     --password admin \
#     --firstname Admin \
#     --lastname User \
#     --role Admin \
#     --email admin@example.com
# '

# # Create MLflow experiment
# echo "Initializing MLflow..."
# docker exec -it mlflow bash -c '
# mlflow experiments create --experiment-name als_anime_recommendation
# '

echo "Setup complete! Services are now running at:"
echo "- Airflow: http://localhost:8080"
echo "- MLflow: http://localhost:5000"
echo "- FastAPI: http://localhost:8000"
echo "- Spark Master: http://localhost:8080"

echo "Default credentials:"
echo "Airflow - username: admin, password: admin"

echo "To train the model, run:"
echo "docker exec -it spark-master bash -c 'source .venv/bin/activate && spark/bin/spark-submit src/als_anime.py'"
docker exec -it spark-master bash -c 'source .venv/bin/activate && spark/bin/spark-submit src/als_anime.py'
docker exec -it spark-master bash -c 'source .venv/bin/activate && spark/bin/spark-submit src/dev.py'
