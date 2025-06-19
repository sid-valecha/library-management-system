import mysql.connector
from sqlalchemy import create_engine, text
# from main import *
import pandas as pd
from contextlib import contextmanager
import os

CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "libuser"),
    "password": os.getenv("DB_PASS"),          # required
    "database": os.getenv("DB_NAME", "library_system"),
}
def get_connection():
    return mysql.connector.connect(**CONFIG)

@contextmanager
def get_conn():
    conn = mysql.connector.connect(**CONFIG)
    try:
        yield conn
    finally:
        conn.close()

def fetchone(query, params=None):
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(query, params or ())
        return cur.fetchone()

def fetchall(query, params=None):
    with get_conn() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(query, params or ())
        return cur.fetchall()

def execute(query, params=None):
    """INSERT/UPDATE/DELETE → returns lastrowid (if any)."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(query, params or ())
        conn.commit()
        return cur.lastrowid