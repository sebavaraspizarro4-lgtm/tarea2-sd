import sqlite3
import time
import numpy as np
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_PATH = "/app/results/metrics.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS events (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp  REAL,
        event      TEXT,
        zone_id    TEXT,
        query_type TEXT,
        latency_ms REAL,
        cache_key  TEXT
    )''')
    conn.commit()
    conn.close()

@app.route("/record", methods=["POST"])
def record():
    body = request.json
    conn = get_db()
    conn.execute(
        "INSERT INTO events (timestamp, event, zone_id, query_type, latency_ms, cache_key) VALUES (?,?,?,?,?,?)",
        (time.time(), body["event"], body.get("zone_id"), body.get("query_type"),
         body.get("latency_ms"), body.get("cache_key"))
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route("/summary")
def summary():
    conn = get_db()
    rows = conn.execute("SELECT event, latency_ms FROM events").fetchall()
    conn.close()
    hits   = [r["latency_ms"] for r in rows if r["event"] == "hit"]
    misses = [r["latency_ms"] for r in rows if r["event"] == "miss"]
    total  = len(hits) + len(misses)
    if total == 0:
        return jsonify({"message": "sin datos aun"})
    latencias = [r["latency_ms"] for r in rows]
    return jsonify({
        "total_queries": total,
        "hits": len(hits),
        "misses": len(misses),
        "hit_rate": round(len(hits) / total, 4),
        "latency_p50_ms": round(float(np.percentile(latencias, 50)), 2),
        "latency_p95_ms": round(float(np.percentile(latencias, 95)), 2),
        "avg_latency_ms": round(float(np.mean(latencias)), 2),
    })

@app.route("/events")
def events():
    limit = request.args.get("limit", 100)
    conn = get_db()
    rows = conn.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5002)
