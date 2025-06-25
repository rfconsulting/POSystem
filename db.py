import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Cambia estos valores por los de tu servidor MySQL
MYSQL_CONFIG = {
    'host': os.getenv('host'),
    'user': os.getenv('user'),
    'password': os.getenv('password'),
    'database': os.getenv('database')
}

def create_connection():
    load_dotenv(override=True)  # Esto recarga las variables cada vez
    try:
        conn = mysql.connector.connect(
            host=os.getenv('host'),
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('database'),
            port=int(os.getenv('port', 3306))
        )
        return conn
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def close_connection(conn):
    if conn and conn.is_connected():
        conn.close()
        print("MySQL connection closed")
    else:
        print("No connection to close")

def create_database():
    try:
        conn = mysql.connector.connect(
            host=MYSQL_CONFIG['host'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password']
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']}")
        print("Database checked/created")
        cursor.close()
        conn.close()
    except Error as e:
        print(f"Error creating database: {e}")

def create_table():
    conn = create_connection()
    if conn:
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS cliente (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            mensaje TEXT,
            archivo VARCHAR(255),
            fecha DATE
        );
        """
        try:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            print("Table checked/created")
            cursor.close()
        except Error as e:
            print(f"Error creating table: {e}")
        close_connection(conn)