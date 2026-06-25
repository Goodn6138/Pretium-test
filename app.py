from fastapi import FastAPI, Request
from datetime import datetime
import os
import json

import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pretium_callbacks (
            id SERIAL PRIMARY KEY,
            transaction_code VARCHAR(100),
            status VARCHAR(50),
            payload JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()

init_db()


@app.get("/")
async def health():
    return {
        "success": True,
        "message": "Pretium callback service running"
    }


@app.post("/api/pretium/callback")
async def callback(request: Request):
    payload = await request.json()

    transaction_code = payload.get("transaction_code")
    status = payload.get("status")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO pretium_callbacks
        (transaction_code, status, payload)
        VALUES (%s, %s, %s)
        """,
        (
            transaction_code,
            status,
            Json(payload)
        )
    )

    conn.commit()
    cur.close()
    conn.close()

    return {
        "success": True,
        "message": "Callback received"
    }


@app.get("/transactions")
async def transactions(limit: int = 20):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            transaction_code,
            status,
            created_at
        FROM pretium_callbacks
        ORDER BY id DESC
        LIMIT %s
    """, (limit,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        {
            "id": r[0],
            "transaction_code": r[1],
            "status": r[2],
            "created_at": r[3]
        }
        for r in rows
    ]
