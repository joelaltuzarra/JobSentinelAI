import sqlite3

DB_NAME = "jobs.db"

def init_db():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_query TEXT,
            title TEXT,
            url TEXT UNIQUE,  -- UNIQUE evita guardar trabajos duplicados
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_jobs(query, jobs_list):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    saved_count = 0
    for job in jobs_list:
        try:
            cursor.execute('''
                INSERT INTO jobs (search_query, title, url, description)
                VALUES (?, ?, ?, ?)
            ''', (query.lower(), job['title'], job['url'], job['description']))
            saved_count += 1
        except sqlite3.IntegrityError:
            # Si el trabajo ya existe (URL duplicada), se ignora
            pass

    conn.commit()
    conn.close()
    return saved_count

def get_jobs_by_query(query):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT title, url, description FROM jobs
        WHERE search_query LIKE ?
    ''', (f"%{query.lower()}%",))

    rows = cursor.fetchall()
    conn.close()

    return [{"title": row[0], "url": row[1], "description": row[2]} for row in rows]

init_db()