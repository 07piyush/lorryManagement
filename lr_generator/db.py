"""Database operations module."""
import psycopg2
from typing import List, Dict
from psycopg2.extras import execute_batch

class Database:
    def __init__(self, connection_params: Dict[str, str], table_name: str):
        self.connection_params = connection_params
        self.table_name = table_name
        self._connection = None

    def connect(self):
        """Establish database connection."""
        if not self._connection or self._connection.closed:
            self._connection = psycopg2.connect(**self.connection_params)
        return self._connection

    def create_tables(self):
        """Create necessary database tables if they don't exist."""
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        lr_id VARCHAR(20) PRIMARY KEY,
                        invoice_number VARCHAR(50) NOT NULL,
                        date DATE NOT NULL,
                        consignor_name VARCHAR(100) NOT NULL,
                        consignee_name VARCHAR(100) NOT NULL,
                        weight DECIMAL(10,2) NOT NULL,
                        packages INTEGER NOT NULL,
                        destination VARCHAR(100) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()

    def insert_records(self, records: List[Dict], batch_size: int = 100):
        """Insert multiple records into the database."""
        with self.connect() as conn:
            with conn.cursor() as cur:
                query = f"""
                    INSERT INTO {self.table_name}
                    (lr_id, invoice_number, date, consignor_name, consignee_name,
                     weight, packages, destination)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = [
                    (
                        record['lr_id'],
                        record['invoice_number'],
                        record['date'],
                        record['consignor_name'],
                        record['consignee_name'],
                        record['weight'],
                        record['packages'],
                        record['destination']
                    )
                    for record in records
                ]
                
                execute_batch(cur, query, values, page_size=batch_size)
                conn.commit()

    def close(self):
        """Close the database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
