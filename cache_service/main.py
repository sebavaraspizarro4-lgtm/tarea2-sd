import redis
import json
import time
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

REDIS_HOST  = os.getenv("REDIS_HOST", "redis")
METRICS_URL = os.getenv("METRICS_URL", "http://metrics:5002")
RESPGEN_URL = os.getenv("RESPGEN_URL", "http://response_generator:5001")
TTL         = int(os.getenv("CACHE_TTL", 60))

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)

def send_metric(event, zone_id, query_type, latency_ms, cache_key):
    try:
        requests.post(f"{METRICS_URL}/record", json={
            "event": event, "zone_id": zone_id,
            "query_type": query_type, "latency_ms": latency_ms,
            "cache_key": cache_key
        }, timeout=1)
    except:
        pass

@app.route("/query", methods=["POST"])
def handle_query():
    body       = request.json
    query_type = body.get("query_type")
    zone_id    = body.get("zone_id")
    conf       = body.get("confidence_min", 0.0)
    bins       = body.get("bins", 5)
    zone_b     = body.get("zone_b", "")

    if query_type == "Q1":
        cache_key = f"count:{zone_id}:conf={conf}"
    elif query_type == "Q2":
        cache_key = f"area:{zone_id}:conf={conf}"
    elif query_type == "Q3":
        cache_key = f"density:{zone_id}:conf={conf}"
    elif query_type == "Q4":
        cache_key = f"compare:density:{zone_id}:{zone_b}:conf={conf}"
    elif query_type == "Q5":
        cache_key = f"confidence_dist:{zone_id}:bins={bins}"
    else:
        return jsonify({"error": "query_type invalido"}), 400

    start  = time.time()
    cached = r.get(cache_key)

    if cached:
        latency_ms = (time.time() - start) * 1000
        send_metric("hit", zone_id, query_type, latency_ms, cache_key)
        return jsonify({"result": json.loads(cached), "source": "cache"})

    resp   = requests.post(f"{RESPGEN_URL}/query", json=body, timeout=10)
    result = resp.json()["result"]
    r.setex(cache_key, TTL, json.dumps(result))

    latency_ms = (time.time() - start) * 1000
    send_metric("miss", zone_id, query_type, latency_ms, cache_key)
    return jsonify({"result": result, "source": "miss"})

@app.route("/health")
def health():
    try:
        r.ping()
        redis_ok = True
    except:
        redis_ok = False
    return jsonify({"status": "ok", "redis": redis_ok})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
