# Tarea 2: Procesamiento y Fallback con Apache Kafka

Curso: Sistemas Distribuidos 2026-1
Profesor: Nicolás Hidalgo

## Descripción

Sistema distribuido de análisis de consultas geoespaciales sobre el dataset Google Open Buildings (Región Metropolitana de Santiago), incorporando Apache Kafka como sistema de mensajería asíncrona con mecanismos de fallback y reintentos.

## Arquitectura

Generador de Tráfico → Kafka → Consumidores → Caché (Redis) → Generador de Respuestas
                                     ↓ falla
                               Topic Reintento → DLQ
                               Métricas (SQLite)

## Servicios

- kafka (9092): Broker de mensajería
- zookeeper (2181): Coordinador de Kafka
- redis (6379): Caché con política LRU
- response_generator (5001): Procesa consultas Q1-Q5
- cache_service (5000): Intercepta y cachea respuestas
- metrics (5002): Registra métricas del sistema
- kafka_producer: Publica consultas en Kafka
- kafka_consumer: Consume y procesa consultas
- retry_consumer: Maneja reintentos y DLQ

## Requisitos

- Docker
- docker-compose

## Despliegue

Clonar el repositorio:
    git clone https://github.com/sebavaraspizarro4-lgtm/tarea2-sd.git
    cd tarea2-sd

Sistema base:
    docker-compose up --build

Con múltiples consumers:
    docker-compose up --build --scale kafka_consumer=3

Con fallas simuladas (cambiar FAIL_RATE=0.3 en docker-compose.yml):
    docker-compose up --build

## Consultar métricas

    curl http://localhost:5002/summary

## Tópicos Kafka

- queries: Consultas principales
- queries_retry: Consultas que fallaron y se reintentan
- queries_dlq: Dead Letter Queue (máx reintentos alcanzado)

## Variables de entorno

- DISTRIBUTION (zipf/uniform): Distribución del generador de tráfico
- NUM_QUERIES: Número de consultas a generar
- FAIL_RATE (0.0-1.0): Tasa de fallas simuladas
- MAX_RETRIES: Máximo de reintentos antes de enviar a DLQ
- CACHE_TTL: Tiempo de vida en caché en segundos

## Resultados

Escenario Base (1 consumer):   Hit Rate 80.34% | p50 7.76ms  | p95 67.39ms
Fallas 30%:                    Hit Rate 68.48% | p50 7.86ms  | p95 74.68ms
3 Consumers:                   Hit Rate 80.67% | p50 7.55ms  | p95 66.75ms
Spike 3000 queries:            Hit Rate 92.37% | p50 7.02ms  | p95 14.89ms
