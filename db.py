# db.py — Supabase Postgres via DATABASE_URL (clean)
from __future__ import annotations
import os, hashlib
import psycopg
from psycopg.rows import dict_row
from psycopg import errors as pg_errors
from typing import Optional

def _db_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set. Export it locally and set it in Reflex Cloud Secrets.")
    return url

def get_conn():
    # one connection per call; safe for Reflex Cloud/serverless
    return psycopg.connect(_db_url(), row_factory=dict_row, autocommit=True)

# ---------- Auth & user CRUD ----------
def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()

def get_user(username: str, password: str):
    with get_conn() as c:
        return c.execute(
            "SELECT username, permission FROM users WHERE username=%s AND password=%s",
            (username, hash_password(password)),
        ).fetchone()

def get_all_users():
    with get_conn() as c:
        return c.execute(
            "SELECT username, permission FROM users ORDER BY username"
        ).fetchall()

def add_user(username: str, password: str, permission: str):
    with get_conn() as c:
        c.execute(
            "INSERT INTO users (username, password, permission) VALUES (%s,%s,%s)",
            (username, hash_password(password), permission),
        )

def update_user_permission(username: str, permission: str):
    with get_conn() as c:
        c.execute("UPDATE users SET permission=%s WHERE username=%s", (permission, username))

def delete_user(username: str):
    with get_conn() as c:
        c.execute("DELETE FROM users WHERE username=%s", (username,))

# ---------- regions CRUD ----------
def fetch_all_regions() -> list[dict]:
    """Fetch all regions from the database."""
    try:
        with get_conn() as c:
            rows = c.execute(
                "SELECT id, region_name FROM regions ORDER BY region_name"
            ).fetchall()
            return [dict(r) for r in rows]
    except pg_errors.UndefinedTable:
        # If table isn't created yet, don't crash the UI
        return []

def add_region(region_name: str):
    """Add a new region to the database."""
    with get_conn() as c:
        c.execute(
            "INSERT INTO regions (region_name) VALUES (%s)",
            (region_name,),
        )

def update_region(region_id: int, region_name: str):
    """Update an existing region in the database."""
    with get_conn() as c:
        c.execute(
            "UPDATE regions SET region_name=%s WHERE id=%s",
            (region_name, region_id),
        )

def delete_region(region_id: int):
    """Delete a region from the database."""
    with get_conn() as c:
        c.execute("DELETE FROM regions WHERE id=%s", (region_id,))

# ---------- pacer_cases ----------
def fetch_all_cases(limit: Optional[int] = None) -> list[dict]:
    sql = "SELECT * FROM pacer_cases ORDER BY date_filed DESC"
    params = None
    if limit is not None:
        sql += " LIMIT %s"
        params = (limit,)
    try:
        with get_conn() as c:
            rows = c.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
    except pg_errors.UndefinedTable:
        # If table isn't created yet, don't crash the UI
        return []