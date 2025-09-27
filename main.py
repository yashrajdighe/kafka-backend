import logging
import uvicorn
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaProducer, KafkaConsumer

from prometheus_client import Counter, Histogram, make_asgi_app, CollectorRegistry
import time

# Simple logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress kafka-python logs below WARNING
logging.getLogger("kafka").setLevel(logging.WARNING)

app = FastAPI()

origins = [
    "http://localhost:5500",  # VSCode live server
    "http://localhost:9090",  # Prometheus server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Domains allowed
    allow_credentials=False,  # Allow cookies, auth headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# expose prometheus metrics at /metrics endpoint

# Create a custom Prometheus registry to avoid duplicate registration on reload
PROM_REGISTRY = CollectorRegistry()

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint"],
    registry=PROM_REGISTRY
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    registry=PROM_REGISTRY
)

# Middleware for request metrics
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    REQUEST_COUNT.labels(request.method, request.url.path).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(time.time() - start_time)

    return response

metrics_app = make_asgi_app(registry=PROM_REGISTRY)
app.mount("/metrics", metrics_app)

# Get Kafka bootstrap server from environment variable
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Initialize Kafka Admin Client
kafka_client = None
producer = None

try:
    kafka_client = KafkaAdminClient(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        client_id="kafka-backend",  # what is client id ?
    )
except Exception as e:
    logger.error(f"Error connecting to Kafka: {e}")


# Middleware to check Kafka connection for relevant endpoints
class KafkaConnectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only check for endpoints starting with /kafka
        if request.url.path.startswith("/kafka") or request.url.path == (
            "/health/kafka"
        ):
            try:
                kafka_client.describe_cluster()
                pass
            except Exception as e:
                logger.error(f"Kafka connection failed. Middleware caught error.")
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "error",
                        "message": "Kafka connection failed. Middleware caught error.",
                    },
                )
        response = await call_next(request)
        return response


app.add_middleware(KafkaConnectionMiddleware)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/health/app", tags=["Health"])
def health_check():
    return JSONResponse(
        status_code=200, content={"status": "ok", "message": "API Server is healthy"}
    )


@app.get("/health/kafka", tags=["Health"])
def kafka_health_check():
    return JSONResponse(
        status_code=200,
        content={"status": "connected", "message": "Kafka connection successful"},
    )


@app.get("/kafka/cluster/describe", tags=["Kafka Admin"])
def describe_cluster():
    try:
        cluster_info = kafka_client.describe_cluster()
        return JSONResponse(status_code=200, content={"cluster_info": cluster_info})
    except Exception as e:
        logger.error(f"Error describing cluster: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to describe cluster due to an error. Check app logs.",
            },
        )


@app.get("/kafka/topics/list", tags=["Kafka Topics"])
def list_topics():
    try:
        topics = kafka_client.list_topics()
        return JSONResponse(status_code=200, content={"topics": topics})
    except Exception as e:
        logger.error(f"Error listing topics: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Failed to list topics due to an error. Check app logs.",
            },
        )


@app.post("/kafka/topic/create", tags=["Kafka Topics"])
def create_topic(topic_name: str, num_partitions: int = 3, replication_factor: int = 1):
    try:
        topic = NewTopic(
            name=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor,
        )
        kafka_client.create_topics([topic])
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"Topic '{topic_name}' created successfully",
            },
        )
    except Exception as topic_exists:
        logger.warning(f"Topic '{topic_name}' already exist: {topic_exists}")
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": f"Topic '{topic_name}' already exist.",
            },
        )
    except Exception as e:
        logger.error(f"Error creating topic '{topic_name}': {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to create topic '{topic_name}'. Check app logs.",
            },
        )


@app.get("/kafka/topic/{topic_name}/metadata", tags=["Kafka Topics"])
def get_topic_metadata(topic_name: str):
    try:
        metadata = kafka_client.describe_topics([topic_name])
        return JSONResponse(status_code=200, content={"metadata": metadata[0]})
    except Exception as e:
        logger.error(f"Error fetching metadata for topic '{topic_name}': {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to fetch metadata for topic '{topic_name}'. Check app logs.",
            },
        )


@app.post("/kafka/topic/{topic_name}/produce", tags=["Kafka Topics"])
def produce_message(topic_name: str, message: str):
    try:
        producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        future = producer.send(topic_name, message.encode("utf-8"))
        result = future.get(
            timeout=10
        )  # Block until a single message is sent (or timeout)
        producer.close()
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"Message sent to topic '{topic_name}'",
                "result": str(result),
            },
        )
    except Exception as topic_not_exist:
        logger.warning(f"Topic '{topic_name}' does not exist: {topic_not_exist}")
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": f"Topic '{topic_name}' does not exist.",
            },
        )
    except Exception as e:
        logger.error(f"Error producing message to topic '{topic_name}': {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to produce message to topic '{topic_name}'. Check app logs.",
            },
        )


@app.get("/kafka/topic/{topic_name}/consume", tags=["Kafka Topics"])
def consume_messages(
    topic_name: str,
    group_id: str = "default-group",
    timeout_ms: int = 1000,
    max_messages: int = 10,
):
    try:
        # check if topic exists
        topics = kafka_client.list_topics()
        if topic_name not in topics:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"Topic '{topic_name}' does not exist.",
                },
            )

        # consume messages from topic
        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            auto_offset_reset="earliest",
            consumer_timeout_ms=timeout_ms,
        )
        messages = []
        for _ in range(max_messages):
            try:
                msg = next(consumer)
                messages.append(msg.value.decode("utf-8"))
            except StopIteration:
                break
        consumer.close()
        return JSONResponse(
            status_code=200, content={"status": "success", "messages": messages}
        )
    except Exception as e:
        logger.error(f"Error consuming messages from topic '{topic_name}': {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to consume messages from topic '{topic_name}'. Check app logs.",
            },
        )


def main():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
