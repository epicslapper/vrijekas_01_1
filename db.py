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


def upsert_variable(key, value, unit=None, category=None, label_en=None, is_input=0):
    """Insert or update a row in `variables` for the given key.

    Keeps existing metadata when updating; when inserting we create a minimal row.
    """
    exists = fetch_one("SELECT 1 FROM variables WHERE key=?", (key,))
    if exists:
        execute("UPDATE variables SET value=?, editable=? WHERE key=?", (value, is_input, key))
    else:
        execute(
            "INSERT INTO variables (key, value, unit, category, label_nl, label_en, editable, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (key, value, unit, category, None, label_en, is_input, ""),
        )