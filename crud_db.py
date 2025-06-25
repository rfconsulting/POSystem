from mysql.connector import Error
from db import create_connection, close_connection

# Consultas SQL para MySQL
querys = {
    "select_all": "SELECT * FROM cfprocli",
    "select_one": "SELECT * FROM cfprocli WHERE id = %s",
    "delete": "DELETE FROM cfprocli WHERE id = %s",
    "update": "UPDATE cfprocli SET nombre = %s, email = %s, mensaje = %s, archivo = %s, fecha = %s WHERE id = %s",
    "insert": "INSERT INTO cfprocli (nombre, email, mensaje, archivo, fecha) VALUES (%s, %s, %s, %s, %s)"
}

def execute_query(conn, query, params=None):
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        print("Consulta ejecutada correctamente")
    except Error as e:
        print(f"Error: {e}")

def fetch_all(conn, query, params=None):
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        return rows
    except Error as e:
        print(f"Error: {e}")
        return None

def fetch_one(conn, query, params=None):
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        row = cursor.fetchone()
        return row
    except Error as e:
        print(f"Error: {e}")
        return None

def delete_record(conn, query, params=None):
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        print("Registro eliminado correctamente")
    except Error as e:
        print(f"Error: {e}")

def update_record(conn, query, params=None):
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        print("Registro actualizado correctamente")
    except Error as e:
        print(f"Error: {e}")

def insert_record(conn, query, params=None):
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        print("Registro insertado correctamente")
    except Error as e:
        print(f"Error: {e}")