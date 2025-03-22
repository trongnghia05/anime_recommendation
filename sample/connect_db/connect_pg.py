import os
import psycopg2

from dotenv import load_dotenv
from psycopg2 import sql, OperationalError

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def create_connection():
    try:
        connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        print("Connection to PostgreSQL successful.")
        return connection

    except OperationalError as e:
        print(f"Error: {e}")
        return None


def insert_data(connection, name, age):
    try:
        cursor = connection.cursor()
        insert_query = """INSERT INTO users (name, age) VALUES (%s, %s);"""
        cursor.execute(insert_query, (name, age))
        connection.commit()
        print("Data inserted successfully.")
        cursor.close()

    except Exception as e:
        print(f"Error: {e}")


def main():
    connection = create_connection()
    if connection:
        insert_data(connection, "Alice", 30)
        insert_data(connection, "Bob", 25)
        connection.close()
        print("Connection closed.")


if __name__ == "__main__":
    main()
