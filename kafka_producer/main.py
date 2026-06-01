import os, time, json, uuid
import numpy as np
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
DISTRIBUTION = os.getenv("DISTRIBUTION", "zipf")
NUM_QUERIES  = int(os.getenv("NUM_QUERIES", 1000))
ZIPF_S       = float(os.getenv("ZIPF_S", 1.5))
TOPIC        = "queries"

ZONES       = ["Z1", "Z2", "Z3", "Z4", "Z5"]
QTYPES      = ["Q1", "Q2", "Q3", "Q4", "Q5"]
CONF_VALUES = [0.0, 0.5, 0.7]

def zipf_weights(n, s):
    w = [1 / ((i + 1) ** s) for i in range(n)]
    t = sum(w)
    return [x / t for x in w]

def generate_query(distribution):
    if distribution == "zipf":
        zone_id = np.random.choice(ZONES, p=zipf_weights(len(ZONES), ZIPF_S))
    else:
        zone_id = np.random.choice(ZONES)
    qtype = np.random.choice(QTYPES)
    conf  = float(np.random.choice(CONF_VALUES))
    query = {
        "id": str(uuid.uuid4()),
        "query_type": qtype,
        "zone_id": zone_id,
        "confidence_min": conf,
        "retry_count": 0,
        "created_at": time.time()
    }
    if qtype == "Q4":
        query["zone_b"] = np.random.choice([z for z in ZONES if z != zone_id])
    if qtype == "Q5":
        query["bins"] = int(np.random.choice([3, 5, 10]))
    return query

def wait_for_kafka():
    print("Esperando Kafka...")
    for _ in range(30):
        try:
            p = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
            p.close()
            print("Kafka listo.")
            return
        except NoBrokersAvailable:
            time.sleep(3)
    raise Exception("Kafka no disponible")

def run():
    wait_for_kafka()
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode()
    )
    print(f"Publicando {NUM_QUERIES} consultas | distribucion={DISTRIBUTION}")
    for i in range(NUM_QUERIES):
        query = generate_query(DISTRIBUTION)
        producer.send(TOPIC, query)
        if (i + 1) % 100 == 0:
            print(f"Publicadas {i+1}/{NUM_QUERIES}")
        time.sleep(0.01)
    producer.flush()
    print("Todas las consultas publicadas.")

if __name__ == "__main__":
    run()
