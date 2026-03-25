import psycopg2
import logging
import sys

logging.basicConfig(level=logging.INFO)

def seed_db():
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=5432,
            dbname="postgres",
            user="postgres",
            password="alloydb"
        )
        conn.autocommit = True
        logging.info("Connected to AlloyDB!")
        
        with open("backend/seed.sql", "r", encoding="utf-8") as f:
            sql = f.read()
        
        with conn.cursor() as cur:
            cur.execute(sql)
            
        logging.info("Seed data applied successfully!")
        conn.close()
    except Exception as e:
        logging.error(f"Failed to seed DB: {e}")
        sys.exit(1)

if __name__ == "__main__":
    seed_db()
