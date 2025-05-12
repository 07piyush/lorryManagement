"""Database setup script."""
import os
import time
import subprocess
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# PostgreSQL paths
PG_BIN = Path(r'D:\Prerequisites\postgreSQL\bin')
DATA_DIR = Path(os.getcwd()) / 'pgdata'

def init_db_cluster():
    """Initialize PostgreSQL data directory."""
    if not DATA_DIR.exists():
        print("Initializing new PostgreSQL data directory...")
        subprocess.run(
            [PG_BIN / 'initdb', '-D', str(DATA_DIR), '--username=postgres', '--encoding=UTF8'],
            check=True
        )
        
        # Update postgresql.conf for local connections
        conf_file = DATA_DIR / 'postgresql.conf'
        with open(conf_file, 'a') as f:
            f.write("\n# Custom settings\n")
            f.write("listen_addresses = 'localhost'\n")
            f.write("port = 5432\n")
    else:
        print("PostgreSQL data directory already exists.")

def start_postgres():
    """Start PostgreSQL server."""
    print("Starting PostgreSQL server...")
    subprocess.Popen(
        [PG_BIN / 'pg_ctl', '-D', str(DATA_DIR), '-l', str(DATA_DIR / 'logfile'), 'start']
    )

    # Wait until server is ready
    for attempt in range(10):
        try:
            conn = psycopg2.connect(
                host='localhost',
                port='5432',
                database='postgres',
                user='postgres'
            )
            conn.close()
            print("PostgreSQL server is running.")
            return
        except Exception as e:
            print(f"Waiting for server (attempt {attempt + 1}/10)...")
            time.sleep(1)
    raise RuntimeError("PostgreSQL server did not start.")

def stop_postgres():
    """Stop PostgreSQL server."""
    print("Stopping PostgreSQL server...")
    subprocess.run(
        [PG_BIN / 'pg_ctl', '-D', str(DATA_DIR), 'stop'],
        check=True
    )

def setup_database():
    """Create database and required tables."""
    # First try to connect to postgres database
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        database='postgres',
        user='postgres'
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = 'lr_generator'")
            if not cur.fetchone():
                cur.execute("CREATE DATABASE lr_generator")
                print("Created database: lr_generator")
    finally:
        conn.close()

    # Continue with table creation (same as your current logic)

if __name__ == '__main__':
    init_db_cluster()
    start_postgres()
    setup_database()
