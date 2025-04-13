from datetime import datetime, timedelta
import pandas as pd
import json
from elasticsearch import Elasticsearch, helpers
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.models import Variable

# DAG default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'anime_elasticsearch_indexing',
    default_args=default_args,
    description='Index anime data from CSV to Elasticsearch',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 4, 13),
    catchup=False,
    tags=['anime', 'elasticsearch'],
)

# Define the elasticsearch connection parameters
# You can also store these in Airflow Variables or Connections
ES_HOST = "http://elasticsearch:9200"
ES_PORT = 9200
ES_INDEX = "anime_with_synopsis_index"
CSV_FILE_PATH = "/opt/airflow/data/movies/anime_with_synopsis.csv"  # Update with actual path


def extract_data(**kwargs):
    """
    Extract data from CSV file and convert to a structured format
    """
    try:
        # Read the CSV file
        df = pd.read_csv(CSV_FILE_PATH)

        # Data processing and cleaning
        df['Genres'] = df['Genres'].str.split(', ')

        # Convert DataFrame to list of dictionaries
        anime_list = df.to_dict('records')

        # Pass the data to the next task
        kwargs['ti'].xcom_push(key='anime_data', value=anime_list)

        print(f"Successfully extracted {len(anime_list)} anime records")
        return anime_list
    except Exception as e:
        print(f"Error in extract_data: {e}")
        raise


def create_elasticsearch_index(**kwargs):
    """
    Create or update Elasticsearch index with proper mappings
    """
    try:
        # Connect to Elasticsearch
        es = Elasticsearch([ES_HOST])

        # Define the index mapping
        mapping = {
            "mappings": {
                "properties": {
                    "MAL_ID": {"type": "keyword"},
                    "Name": {
                        "type": "text",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "Score": {"type": "float"},
                    "Genres": {"type": "keyword"},
                    "sypnopsis": {
                        "type": "text",
                        "analyzer": "standard"
                    }
                }
            }
        }

        # Check if index exists
        if es.indices.exists(index=ES_INDEX):
            print(f"Index {ES_INDEX} already exists. Deleting and recreating...")
            es.indices.delete(index=ES_INDEX)

        # Create the index with the mapping
        es.indices.create(index=ES_INDEX, body=mapping)
        print(f"Successfully created index {ES_INDEX} with mappings")

    except Exception as e:
        print(f"Error in create_elasticsearch_index: {e}")
        raise


def index_data_to_elasticsearch(**kwargs):
    """
    Index all anime data to Elasticsearch
    """
    try:
        # Get the anime data from the previous task
        ti = kwargs['ti']
        anime_list = ti.xcom_pull(key='anime_data', task_ids='extract_data')

        # Connect to Elasticsearch
        es = Elasticsearch([ES_HOST])

        # Prepare the actions for bulk indexing
        actions = [
            {
                "_index": ES_INDEX,
                "_id": anime["MAL_ID"],
                "_source": {
                    "MAL_ID": anime["MAL_ID"],
                    "Name": anime["Name"],
                    "Score": anime["Score"],
                    "Genres": anime["Genres"],
                    "sypnopsis": anime["sypnopsis"]
                }
            }
            for anime in anime_list
        ]

        # Bulk index the data
        success, failed = helpers.bulk(es, actions, stats_only=True, raise_on_error=False)

        print(f"Successfully indexed {success} anime entries to Elasticsearch")
        if failed > 0:
            print(f"Failed to index {failed} anime entries")

    except Exception as e:
        print(f"Error in index_data_to_elasticsearch: {e}")
        raise


def verify_elasticsearch_data(**kwargs):
    """
    Verify that data was correctly indexed to Elasticsearch
    """
    try:
        # Connect to Elasticsearch
        es = Elasticsearch([ES_HOST])

        # Check the number of documents in the index
        count = es.count(index=ES_INDEX)
        print(f"Number of documents in index {ES_INDEX}: {count['count']}")

        # Perform a simple search to verify data quality
        sample_search = es.search(
            index=ES_INDEX,
            body={
                "query": {
                    "match_all": {}
                },
                "size": 1
            }
        )

        # Print a sample document
        if sample_search['hits']['total']['value'] > 0:
            print("Sample document:")
            print(json.dumps(sample_search['hits']['hits'][0]['_source'], indent=2))

    except Exception as e:
        print(f"Error in verify_elasticsearch_data: {e}")
        raise


# Define the tasks
extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    provide_context=True,
    dag=dag,
)

create_index_task = PythonOperator(
    task_id='create_elasticsearch_index',
    python_callable=create_elasticsearch_index,
    provide_context=True,
    dag=dag,
)

index_data_task = PythonOperator(
    task_id='index_data_to_elasticsearch',
    python_callable=index_data_to_elasticsearch,
    provide_context=True,
    dag=dag,
)

verify_data_task = PythonOperator(
    task_id='verify_elasticsearch_data',
    python_callable=verify_elasticsearch_data,
    provide_context=True,
    dag=dag,
)

# Task dependencies
extract_task >> create_index_task >> index_data_task >> verify_data_task