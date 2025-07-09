import psycopg2

def setup_postgres():
    conn = psycopg2.connect(
        dbname="source_db",
        user="user",
        password="password",
        host="localhost",
        port=5432
    )
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS public.my_table (
            id SERIAL PRIMARY KEY,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    cur.execute("INSERT INTO public.my_table (name) VALUES (%s), (%s);", ('Alice', 'Bob'))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Таблица создана и данные вставлены.")


if __name__ == '__main__':
    setup_postgres()