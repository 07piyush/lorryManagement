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
                        record['lr_id'],
                        record['invoice_number'],
                        record['receive_date'],
                        record.get('time'),
                        record.get('brand'),
                        record['party_name'],
                        record['location'],
                        record['boxes'],
                        record['transporter'],
                        record.get('transit_time'),
                        record.get('eway_bill'),
                        record.get('pin_code'),
                        record.get('amount'),
                        record['weight'],
                        record.get('lr_no'),
                        record.get('remark'),
                        record.get('status'),
                        record.get('delivery_date')
                    )
                    for record in records
                ]
                
                execute_batch(cur, query, values, page_size=batch_size)
                conn.commit()

    def close(self):
        """Close the database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
