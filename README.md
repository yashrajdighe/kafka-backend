# Kafka Backend FastAPI

A FastAPI backend for interacting with Kafka clusters.

## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (for dependency management)
- Docker & Docker Compose (for containerized development)

## Monitoring & Observability

- **Prometheus** is integrated for metrics scraping. FastAPI exposes metrics at [`/metrics`](http://localhost:8000/metrics).
- **Grafana** is available for dashboarding (default credentials: `admin/admin`).
- Prometheus and Grafana are started via Docker Compose and pre-configured to monitor the FastAPI backend.

### Prometheus Configuration

- Main Compose: `prometheus/prometheus.yml` (targets FastAPI at `fastapi:8000`)
- Dev Compose: `dev/prometheus/prometheus.yml` (targets FastAPI at `localhost:8000`)

### Accessing Dashboards

- **Prometheus UI:** [http://localhost:9090](http://localhost:9090)
- **Grafana UI:** [http://localhost:3000](http://localhost:3000)

## Local Development

### Install dependencies

```sh
make install
```

### Run the app locally

```sh
make run-dev
```

This uses `uv run main.py` for hot-reload development.

#### Stop dev containers

```sh
make stop-dev
```

### Format and lint

```sh
make format
make lint
```

## Docker Development

### Build and start services

```sh
docker compose up --build
```

- Kafka broker will be available at `broker:9092` (internal Docker network).
- FastAPI backend will be available at `localhost:8000`.
- Prometheus will be available at `localhost:9090`.
- Grafana will be available at `localhost:3000`.

#### Metrics endpoint

- FastAPI exposes Prometheus metrics at [`/metrics`](http://localhost:8000/metrics).

#### Prometheus scrape config

- See `prometheus/prometheus.yml` and `dev/prometheus/prometheus.yml` for details.

### Environment Variables

- `KAFKA_BOOTSTRAP_SERVERS` (default: `broker:9092` in Docker, `localhost:9092` locally)

## Useful Makefile Commands

- `make install` — Install dependencies
- `make run` — Run FastAPI app (production style)
- `make run-dev` — Run FastAPI app (development/hot-reload)
- `make stop-dev` — Stop dev Docker Compose services
- `make format` — Format code with Black
- `make lint` — Lint code with Flake8

## API Endpoints

See `main.py` for available endpoints for Kafka cluster, topics, health checks, produce/consume, etc.

### Monitoring endpoints

- `/metrics` — Prometheus metrics for FastAPI (request count, latency, etc.)

## Notes

- Ensure Kafka broker is running before using Kafka endpoints.
- For local development, you may need to run Kafka separately or use Docker Compose.

- Prometheus and Grafana are now included in both main and dev Docker Compose setups.
- Prometheus scrapes FastAPI metrics at `/metrics`.
