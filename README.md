# Kafka Backend FastAPI

A FastAPI backend for interacting with Kafka clusters.

## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (for dependency management)
- Docker & Docker Compose (for containerized development)

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

### Environment Variables

- `KAFKA_BOOTSTRAP_SERVERS` (default: `broker:9092` in Docker, `localhost:9092` locally)

## Useful Makefile Commands

- `make install` — Install dependencies
- `make run` — Run FastAPI app (production style)
- `make run-dev` — Run FastAPI app (development/hot-reload)
- `make format` — Format code with Black
- `make lint` — Lint code with Flake8

## API Endpoints

See `main.py` for available endpoints for Kafka cluster, topics, health checks, produce/consume, etc.

## Notes

- Ensure Kafka broker is running before using Kafka endpoints.
- For local development, you may need to run Kafka separately or use Docker Compose.

# License

MIT
