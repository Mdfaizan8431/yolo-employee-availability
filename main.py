from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
from datetime import datetime

app = FastAPI(title="Employee Presence API")

DB_CONFIG = {
    "host": "localhost",
    "user": "yolo_user",
    "password": "1234",
    "dbname": "yolo_db",   # ✅ updated
    "port": 5432    
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.post("/employee/entry")
def employee_entry(data: dict):
    tracking_id = data["tracking_id"]
    time = data["time"]

    conn = get_connection()
    cur = conn.cursor()

    # INSERT ENTRY ONLY IF NOT ALREADY OPEN
    cur.execute("""
        INSERT INTO events (tracking_id, entry_time, status)
        VALUES (%s, %s, 'ENTRY')
    """, (tracking_id, time))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "ENTRY saved"}

@app.post("/employee/exit")
def employee_exit(data: dict):
    tracking_id = data["tracking_id"]
    time = data["time"]

    conn = get_connection()
    cur = conn.cursor()

    # UPDATE LAST OPEN ENTRY
    cur.execute("""
        UPDATE events
        SET exit_time = %s,
            status = 'EXIT'
        WHERE id = (
            SELECT id FROM events
            WHERE tracking_id = %s AND status = 'ENTRY'
            ORDER BY entry_time DESC
            LIMIT 1
        )
    """, (time, tracking_id))

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "EXIT saved"}
