#######################################################################################
# This script...
# 1. connects to the cop database
# 2. enables add, edit, and delete users functions
#######################################################################################
import sqlite3
import hashlib

DB_PATH = "cop.db"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user(username, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, permission FROM users WHERE username=? AND password=?", 
                (username, hash_password(password)))
    user = cur.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, permission FROM users")
    users = cur.fetchall()
    conn.close()
    return users

def add_user(username, password, permission):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, password, permission) VALUES (?, ?, ?)", 
                (username, hash_password(password), permission))
    conn.commit()
    conn.close()

def update_user_permission(username, permission):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET permission=? WHERE username=?", (permission, username))
    conn.commit()
    conn.close()

def delete_user(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()
