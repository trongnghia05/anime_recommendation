from datetime import datetime, timedelta
import pandas as pd
import sys
import os

# Append the Airflow path
sys.path.append('/opt/airflow')

from airflow import DAG
from airflow.operators.python_operator import PythonOperator

# Default arguments with your specified settings
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define DAG with your specified settings
dag = DAG(
    'import_anime_data',
    default_args=default_args,
    description='DAG cho hệ thống đề xuất anime với MLflow',
    schedule_interval='0 0 * * *',  # Chạy hàng ngày vào lúc 00:00
    catchup=False,
)


def create_anime_tables(**kwargs):
    """Create anime and animelist tables if they don't exist"""
    import psycopg2

    conn = psycopg2.connect(
        host="postgres",
        database="airflow",
        user="airflow",
        password="airflow",
        port=5432
    )

    cursor = conn.cursor()

    # Create anime table SQL with column names properly quoted
    create_anime_table_sql = '''
    CREATE TABLE IF NOT EXISTS anime (
        "mal_id" INTEGER PRIMARY KEY,
        "name" TEXT,
        "score" FLOAT,
        "genres" TEXT,
        "english_name" TEXT,
        "japanese_name" TEXT,
        "type" TEXT,
        "episodes" INTEGER,
        "aired" TEXT,
        "premiered" TEXT,
        "producers" TEXT,
        "licensors" TEXT,
        "studios" TEXT,
        "source" TEXT,
        "duration" TEXT,
        "rating" TEXT,
        "ranked" INTEGER,
        "popularity" INTEGER,
        "members" INTEGER,
        "favorites" INTEGER,
        "watching" INTEGER,
        "completed" INTEGER,
        "on_hold" INTEGER,
        "dropped" INTEGER,
        "plan_to_watch" INTEGER,
        "score_10" INTEGER,
        "score_9" INTEGER,
        "score_8" INTEGER,
        "score_7" INTEGER,
        "score_6" INTEGER,
        "score_5" INTEGER,
        "score_4" INTEGER,
        "score_3" INTEGER,
        "score_2" INTEGER,
        "score_1" INTEGER
    );
    '''

    # Create animelist table SQL with column names properly quoted
    create_animelist_table_sql = '''
    CREATE TABLE IF NOT EXISTS animelist (
        "id" SERIAL PRIMARY KEY,
        "user_id" INTEGER,
        "anime_id" INTEGER,
        "rating" INTEGER,
        "watching_status" INTEGER,
        "watched_episodes" INTEGER
    );
    '''

    # Drop tables if they exist
    cursor.execute("DROP TABLE IF EXISTS anime;")
    cursor.execute("DROP TABLE IF EXISTS animelist;")
    conn.commit()

    # Create tables
    cursor.execute(create_anime_table_sql)
    cursor.execute(create_animelist_table_sql)
    conn.commit()

    cursor.close()
    conn.close()

    return "Anime tables created successfully"


# Task to create the anime tables
create_tables_task = PythonOperator(
    task_id='create_anime_tables',
    python_callable=create_anime_tables,
    provide_context=True,
    dag=dag,
)


def process_and_load_anime_data(**kwargs):
    """Process anime CSV and load into database"""
    import psycopg2
    from psycopg2.extras import execute_values

    # Define the path to the CSV file in the data folder
    csv_path = '/opt/airflow/data/movies/anime.csv'

    # Read the CSV file
    df = pd.read_csv(csv_path, encoding='utf-8')

    # Print column names for debugging
    print("Original column names in CSV:", df.columns.tolist())

    # Rename columns to lowercase and replace spaces/hyphens with underscores
    column_mapping = {
        col: col.lower().replace(' ', '_').replace('-', '_')
        for col in df.columns
    }
    df = df.rename(columns=column_mapping)

    # Print renamed columns for debugging
    print("Renamed columns:", df.columns.tolist())

    # Clean the data - Replace NaN values with appropriate defaults
    # Using the renamed columns
    df = df.fillna({
        'mal_id': 0,
        'episodes': 0,
        'score': 0,
        'ranked': 0,
        'popularity': 0,
        'members': 0,
        'favorites': 0,
        'watching': 0,
        'completed': 0,
        'on_hold': 0,
        'dropped': 0,
        'plan_to_watch': 0,
        'score_10': 0,
        'score_9': 0,
        'score_8': 0,
        'score_7': 0,
        'score_6': 0,
        'score_5': 0,
        'score_4': 0,
        'score_3': 0,
        'score_2': 0,
        'score_1': 0
    })

    # Define columns that should be float
    float_columns = ['score']

    # Define columns that should be integer
    int_columns = [
        'mal_id', 'episodes', 'ranked', 'popularity', 'members',
        'favorites', 'watching', 'completed', 'on_hold', 'dropped',
        'plan_to_watch', 'score_10', 'score_9', 'score_8', 'score_7',
        'score_6', 'score_5', 'score_4', 'score_3', 'score_2', 'score_1'
    ]

    # Convert float columns
    for col in float_columns:
        if col in df.columns:
            # Replace 'Unknown' with NaN, then convert to float
            df[col] = pd.to_numeric(df[col].replace('Unknown', pd.NA), errors='coerce').fillna(0)

    # Convert integer columns
    for col in int_columns:
        if col in df.columns:
            # Replace 'Unknown' with NaN, then convert to float, then to int
            df[col] = pd.to_numeric(df[col].replace('Unknown', pd.NA), errors='coerce').fillna(0).astype(int)

    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host="postgres",
        database="airflow",
        user="airflow",
        password="airflow",
        port=5432
    )

    cursor = conn.cursor()

    # Truncate the table to avoid duplicates
    cursor.execute('TRUNCATE TABLE anime')

    # Get column names from dataframe
    columns = df.columns.tolist()

    # Create a placeholder string for the SQL query
    placeholders = ', '.join(['%s'] * len(columns))

    # Construct the column name part of the SQL query
    column_names = ', '.join([f'"{col}"' for col in columns])

    # Construct the SQL INSERT statement
    insert_stmt = f"""
    INSERT INTO anime ({column_names})
    VALUES ({placeholders})
    """

    # Convert dataframe to a list of tuples for insertion
    records = [tuple(row) for row in df.values]

    # Execute the bulk insert
    cursor.executemany(insert_stmt, records)

    # Commit the transaction
    conn.commit()

    # Close connection
    cursor.close()
    conn.close()

    return f"Successfully loaded {len(df)} anime records"


def process_and_load_animelist_data(**kwargs):
    """Process animelist CSV and load into database"""
    import psycopg2
    from psycopg2.extras import execute_values

    # Define the path to the CSV file in the data folder
    csv_path = '/opt/airflow/data/movies/animelist.csv'

    # Read the CSV file
    df = pd.read_csv(csv_path, encoding='utf-8')

    # Print column names for debugging
    print("Original animelist columns:", df.columns.tolist())

    # Clean the data - Replace NaN values with appropriate defaults
    df = df.fillna({
        'user_id': 0,
        'anime_id': 0,
        'rating': 0,
        'watching_status': 0,
        'watched_episodes': 0
    })

    # Convert all columns to integers
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host="postgres",
        database="airflow",
        user="airflow",
        password="airflow",
        port=5432
    )

    cursor = conn.cursor()

    # Truncate the table to avoid duplicates
    cursor.execute('TRUNCATE TABLE animelist')

    # Get column names from dataframe
    columns = df.columns.tolist()

    # Create a placeholder string for the SQL query
    placeholders = ', '.join(['%s'] * len(columns))

    # Construct the column name part of the SQL query
    column_names = ', '.join([f'"{col}"' for col in columns])

    # Construct the SQL INSERT statement
    insert_stmt = f"""
    INSERT INTO animelist ({column_names})
    VALUES ({placeholders})
    """

    # Convert dataframe to a list of tuples for insertion

    records = []
    for i, row in df.iterrows():
        # Convert each column value to a native Python int
        native_row = tuple(int(val) for val in row)
        records.append(native_row)

    # Execute the bulk insert
    cursor.executemany(insert_stmt, records)

    # Commit the transaction
    conn.commit()

    # Close connection
    cursor.close()
    conn.close()

    return f"Successfully loaded {len(df)} animelist records"


# Task to process and load the anime data
process_load_anime = PythonOperator(
    task_id='process_and_load_anime_data',
    python_callable=process_and_load_anime_data,
    provide_context=True,
    dag=dag,
)

# Task to process and load the animelist data
process_load_animelist = PythonOperator(
    task_id='process_and_load_animelist_data',
    python_callable=process_and_load_animelist_data,
    provide_context=True,
    dag=dag,
)

# Define dependencies
create_tables_task >> process_load_anime
create_tables_task >> process_load_animelist