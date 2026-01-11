from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
from fastapi.responses import HTMLResponse

# -------------------------
# DATABASE CONFIG
# -------------------------
DB_CONFIG = {
    "host": "localhost",
    "database": "yolo_db",
    "user": "yolo_user",
    "password": "yolo123"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            time TIMESTAMP,
            status TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def save_event(status, time):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (time, status) VALUES (%s, %s)",
        (time, status)
    )
    conn.commit()
    cur.close()
    conn.close()

# -------------------------
# FASTAPI APP
# -------------------------
app = FastAPI(title="Employee Presence API")

@app.on_event("startup")
def startup_event():
    init_db()

class Event(BaseModel):
    status: str
    time: str

@app.get("/")
def root():
    return {"message": "Employee Presence API is running"}

@app.post("/employee")
def employee_event(event: Event):
    save_event(event.status, event.time)
    return {"message": "Employee event saved to PostgreSQL"}

@app.get("/stream", response_class=HTMLResponse)
def stream_page():
    with open("templates/stream.html", "r") as f:
        return f.read()
