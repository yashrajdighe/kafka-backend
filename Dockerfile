FROM python:3.14-slim

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:0.8.19 /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
RUN apt update && apt install build-essential -y --no-install-recommends
WORKDIR /app
RUN make install

# Run the application.
CMD ["make", "run"]
