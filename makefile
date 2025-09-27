# Variables
PYTHON=$(shell which python)
PIP=$(shell which pip)
APP=main:app
UVICORN=uvicorn


.PHONY: run # this is only for docker-compose
run:
	/app/.venv/bin/fastapi run /app/main.py
# 	/app/.venv/bin/fastapi run /app/main.py --port 8000 --host 0.0.0.0

.PHONY: run-dev
run-dev:
	docker-compose -f ./dev/docker-compose.yaml up -d
	uv run main.py

.PHONY: stop-dev
stop-dev:
	docker-compose -f ./dev/docker-compose.yaml down

.PHONY: install
install:
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "uv not found. Installing..."; \
		curl -LsSf https://astral.sh/uv/0.8.19/install.sh | sh; \
	else \
		echo "uv already installed."; \
	fi
	uv sync --frozen --no-cache
	@if ! command -v black >/dev/null 2>&1; then \
		echo "black not found. Installing..."; \
		$(PIP) install black; \
	else \
		echo "black already installed."; \
	fi
	@if ! command -v flake8 >/dev/null 2>&1; then \
		echo "flake8 not found. Installing..."; \
		$(PIP) install flake8; \
	else \
		echo "flake8 already installed."; \
	fi
	@if ! command -v uvicorn >/dev/null 2>&1; then \
		echo "uvicorn not found. Installing..."; \
		$(PIP) install uvicorn; \
	else \
		echo "uvicorn already installed."; \
	fi

.PHONY: format
format:
	$(PYTHON) -m black .

.PHONY: lint
lint:
	$(PYTHON) -m flake8 .
