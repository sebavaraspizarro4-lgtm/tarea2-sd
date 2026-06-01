import os, time, json, random, requests
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
CACHE_URL    = os.getenv("CACHE_URL", "http://cache_service:5000")
METRICS_URL  = os.getenv("METRICS_URL", "http://metrics:5002")
MAX_RETRIES  = int(os.getenv("MAX_RETRIES", 3))
FAIL_RATE    = float(os.getenv("FAIL_RATE", 0.0))

TOPIC        = "queries"
RETRY_TOPIC  = "queries_retry"
DLQ_TOPIC    = "queries_dlq"
GROUP_ID     = "query_consumers"

def send_metric(event, query_id, latency_ms, query_type=None, zone_id=None):
    try:
        requests.post(f"{METRICS_URL}/record", json={
            "event": event, "cache_key": query_id,
            "latency_ms": latency_ms,
            "query_type": query_type, "zone_id": zone_id
        }, timeout=1)
    except:
        pass

def wait_for_kafka():
    print("Consumer esperando Kafka...")
    for _ in range(30):
        try:
            p = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
            p.close()
            return
        except NoBrokersAvailable:
            time.sleep(3)

def run():
    wait_for_kafka()
    time.sleep(5)

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        group_id=GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode()),
        auto_offset_reset="earliest",
        enable_auto_commit=True
    )
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode()
    )

    print(f"Consumer listo. Escuchando '{TOPIC}' | fail_rate={FAIL_RATE}")

    for msg in consumer:
        query = msg.value
        qid   = query.get("id", "unknown")
        qtype = query.get("query_type")
        zone  = query.get("zone_id")
        start = time.time()

        # Simular falla aleatoria
        if FAIL_RATE > 0 and random.random() < FAIL_RATE:
            query["retry_count"] = query.get("retry_count", 0) + 1
            if query["retry_count"] >= MAX_RETRIES:
                producer.send(DLQ_TOPIC, query)
                send_metric("dlq", qid, 0, qtype, zone)
                print(f"[DLQ] {qid} tras {query['retry_count']} intentos")
            else:
                producer.send(RETRY_TOPIC, query)
                send_metric("retry", qid, 0, qtype, zone)
                print(f"[RETRY] {qid} intento {query['retry_count']}")
            continue

        try:
            resp = requests.post(f"{CACHE_URL}/query", json=query, timeout=10)
            latency_ms = (time.time() - start) * 1000
            source = resp.json().get("source", "miss")
            send_metric(source, qid, latency_ms, qtype, zone)
            print(f"[OK] {qtype} zone={zone} source={source} {latency_ms:.1f}ms")
        except Exception as e:
            query["retry_count"] = query.get("retry_count", 0) + 1
            if query["retry_count"] >= MAX_RETRIES:
                producer.send(DLQ_TOPIC, query)
                send_metric("dlq", qid, 0, qtype, zone)
                print(f"[DLQ] {qid}: {e}")
            else:
                producer.send(RETRY_TOPIC, query)
                send_metric("retry", qid, 0, qtype, zone)
                print(f"[RETRY] {qid} intento {query['retry_count']}: {e}")

if __name__ == "__main__":
    run()
