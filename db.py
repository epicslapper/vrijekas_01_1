import sqlite3
from pathlib import Path

DB_PATH = Path("vrijekas.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def fetch_all(query, params=()):
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.fetchall()


def fetch_one(query, params=()):
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.fetchone()


def execute(query, params=()):
    with get_conn() as conn:
        conn.execute(query, params)
        conn.commit()