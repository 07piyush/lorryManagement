"""Database operations module."""
import psycopg2
from typing import List, Dict
from psycopg2.extras import execute_batch
from datetime import date, time
import pandas as pd

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
                        receive_date DATE NOT NULL,
                        time TIME,
                        brand VARCHAR(100),
                        party_name VARCHAR(200) NOT NULL,
                        location VARCHAR(100) NOT NULL,
                        boxes INTEGER NOT NULL,
                        transporter VARCHAR(100) NOT NULL,
                        transit_time DATE,
                        eway_bill VARCHAR(50),
                        pin_code INTEGER,
                        amount DECIMAL(10,2),
                        weight VARCHAR(20) NOT NULL,
                        lr_no VARCHAR(50),
                        remark TEXT,
                        status VARCHAR(50),
                        delivery_date DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(invoice_number)
                    )
                """)
                conn.commit()

    def _clean_value(self, value):
        """Clean value for database insertion."""
        if pd.isna(value) or value == '':
            return None
        if isinstance(value, (date, time)):
            return value
        return str(value)

    def insert_records(self, records: List[Dict], batch_size: int = 100):
        """Insert multiple records into the database."""
        with self.connect() as conn:
            with conn.cursor() as cur:
                query = f"""
                    INSERT INTO {self.table_name}
                    (lr_id, invoice_number, receive_date, time, brand, party_name,
                     location, boxes, transporter, transit_time, eway_bill, pin_code,
                     amount, weight, lr_no, remark, status, delivery_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (invoice_number) DO UPDATE SET
                    receive_date = EXCLUDED.receive_date,
                    time = EXCLUDED.time,
                    brand = EXCLUDED.brand,
                    party_name = EXCLUDED.party_name,
                    location = EXCLUDED.location,
                    boxes = EXCLUDED.boxes,
                    transporter = EXCLUDED.transporter,
                    transit_time = EXCLUDED.transit_time,
                    eway_bill = EXCLUDED.eway_bill,
                    pin_code = EXCLUDED.pin_code,
                    amount = EXCLUDED.amount,
                    weight = EXCLUDED.weight,
                    lr_no = EXCLUDED.lr_no,
                    remark = EXCLUDED.remark,
                    status = EXCLUDED.status,
                    delivery_date = EXCLUDED.delivery_date
                """
                
                values = [
                    (
                        self._clean_value(record['lr_id']),
                        self._clean_value(record['invoice_number']),
                        self._clean_value(record['receive_date']),
                        self._clean_value(record.get('time')),
                        self._clean_value(record.get('brand')),
                        self._clean_value(record['party_name']),
                        self._clean_value(record['location']),
                        self._clean_value(record['boxes']),
                        self._clean_value(record['transporter']),
                        self._clean_value(record.get('transit_time')),
                        self._clean_value(record.get('eway_bill')),
                        self._clean_value(record.get('pin_code')),
                        self._clean_value(record.get('amount')),
                        self._clean_value(record['weight']),
                        self._clean_value(record.get('lr_no')),
                        self._clean_value(record.get('remark')),
                        self._clean_value(record.get('status')),
                        self._clean_value(record.get('delivery_date'))
                    )
                    for record in records
                ]
                
                execute_batch(cur, query, values, page_size=batch_size)
                conn.commit()

    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
