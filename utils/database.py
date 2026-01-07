import sqlite3
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "attendance.db")
DB_PATH = os.path.abspath(DB_PATH)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # -------------------- STUDENTS TABLE --------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            prn TEXT PRIMARY KEY,
            roll_no TEXT NOT NULL,
            name TEXT NOT NULL,
            class TEXT NOT NULL,
            division TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            photo BLOB
        )
    """)

    # -------------------- TEACHERS TABLE --------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            subject TEXT,
            password TEXT NOT NULL
        )
    """)

    # -------------------- SUBJECTS TABLE --------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    # -------------------- GROUP PHOTOS TABLE --------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS group_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            class TEXT NOT NULL,
            division TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            photo BLOB NOT NULL,
            location TEXT,
            latitude REAL,
            longitude REAL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (teacher_id) REFERENCES teachers(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )
    """)

    # -------------------- ATTENDANCE TABLE (FINAL VERSION) --------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prn TEXT NOT NULL,
            subject_id INTEGER NOT NULL,
            teacher_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT CHECK(status IN ('Present','Absent')) NOT NULL,
            remarks TEXT,
            photo BLOB,
            location TEXT,
            latitude REAL,
            longitude REAL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (prn) REFERENCES students(prn),
            FOREIGN KEY (subject_id) REFERENCES subjects(id),
            FOREIGN KEY (teacher_id) REFERENCES teachers(id),
            UNIQUE(prn, subject_id, date)
        )
    """)

    conn.commit()
    conn.close()
    print("\n🟢 DATABASE FIXED SUCCESSFULLY!\n")

if __name__ == "__main__":
    init_db()
