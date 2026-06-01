import pandas as pd
import numpy as np
import time
import redis
import json
from flask import Flask, request, jsonify

app = Flask(__name__)


cache = redis.Redis(host='redis', port=6379, db=0)


ZONES = {
    "Z1": {"lat_min": -33.445, "lat_max": -33.420, "lon_min": -70.640, "lon_max": -70.600, "name": "Providencia"},
    "Z2": {"lat_min": -33.420, "lat_max": -33.390, "lon_min": -70.600, "lon_max": -70.550, "name": "Las Condes"},
    "Z3": {"lat_min": -33.530, "lat_max": -33.490, "lon_min": -70.790, "lon_max": -70.740, "name": "Maipú"},
    "Z4": {"lat_min": -33.460, "lat_max": -33.430, "lon_min": -70.670, "lon_max": -70.630, "name": "Santiago Centro"},
    "Z5": {"lat_min": -33.470, "lat_max": -33.430, "lon_min": -70.810, "lon_max": -70.760, "name": "Pudahuel"},
}

def calc_area_km2(bbox):
    lat_diff = abs(bbox["lat_max"] - bbox["lat_min"]) * 111
    lon_diff = abs(bbox["lon_max"] - bbox["lon_min"]) * 111 * np.cos(np.radians((bbox["lat_min"] + bbox["lat_max"]) / 2))
    return lat_diff * lon_diff

ZONE_AREA_KM2 = {zid: calc_area_km2(bbox) for zid, bbox in ZONES.items()}


print("Cargando dataset en memoria...")
df = pd.read_csv("/app/data/santiago_buildings.csv")
DATA = {zid: df[df.zone_id == zid].to_dict("records") for zid in ZONES}
print(f"Dataset cargado: {len(df):,} edificios")


def q1_count(zone_id, confidence_min=0.0):
    return sum(1 for r in DATA[zone_id] if r["confidence"] >= confidence_min)

def q2_area(zone_id, confidence_min=0.0):
    areas = [r["area_in_meters"] for r in DATA[zone_id] if r["confidence"] >= confidence_min]
    if not areas: return {"avg_area": 0, "total_area": 0, "n": 0}
    return {"avg_area": round(float(np.mean(areas)), 4), "total_area": round(float(np.sum(areas)), 4), "n": len(areas)}

def q3_density(zone_id, confidence_min=0.0):
    count = q1_count(zone_id, confidence_min)
    return round(count / ZONE_AREA_KM2[zone_id], 4)

def q4_compare(zone_a, zone_b, confidence_min=0.0):
    da = q3_density(zone_a, confidence_min)
    db = q3_density(zone_b, confidence_min)
    return {"zone_a": da, "zone_b": db, "winner": zone_a if da > db else zone_b}

def q5_confidence_dist(zone_id, bins=5):
    scores = [r["confidence"] for r in DATA[zone_id]]
    counts, edges = np.histogram(scores, bins=bins, range=(0, 1))
    return [{"bucket": i, "min": round(float(edges[i]), 3), "max": round(float(edges[i+1]), 3), "count": int(counts[i])} for i in range(bins)]



@app.route("/query", methods=["POST"])
def handle_query():
    body = request.json
    cache_key = json.dumps(body, sort_keys=True)


    try:

        cached_res = cache.get(cache_key)
        if cached_res:

            return jsonify({
                "result": json.loads(cached_res), 
                "source": "hit"
            })
    except Exception as e:
        print(f"Error al leer de Redis: {e}")


    qtype   = body.get("query_type")
    zone_id = body.get("zone_id")
    conf    = float(body.get("confidence_min", 0.0))
    bins    = int(body.get("bins", 5))
    zone_b  = body.get("zone_b")


    time.sleep(0.05)

    if qtype == "Q1":
        result = q1_count(zone_id, conf)
    elif qtype == "Q2":
        result = q2_area(zone_id, conf)
    elif qtype == "Q3":
        result = q3_density(zone_id, conf)
    elif qtype == "Q4":
        result = q4_compare(zone_id, zone_b, conf)
    elif qtype == "Q5":
        result = q5_confidence_dist(zone_id, bins)
    else:
        return jsonify({"error": "query_type inválido"}), 400


    try:

        cache.set(cache_key, json.dumps(result), ex=3600)
    except Exception as e:
        print(f"Error al escribir en Redis: {e}")


    return jsonify({
        "result": result, 
        "source": "miss"
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "ok", 
        "zones": list(DATA.keys()),
        "total_buildings": sum(len(v) for v in DATA.values())
    })

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5001)
