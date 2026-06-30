import sqlite3

def init_db():
    conn = sqlite3.connect("placement.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT,
    package REAL,
    visit_date TEXT,
    eligibility TEXT,
    user_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
    ''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS prep_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER,
        dsa_done INTEGER DEFAULT 0,
        resume_done INTEGER DEFAULT 0,
        hr_done INTEGER DEFAULT 0,
        notes TEXT,
        FOREIGN KEY(company_id) REFERENCES companies(id)
    )''')

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,

    email TEXT UNIQUE NOT NULL,

    password TEXT NOT NULL

    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()