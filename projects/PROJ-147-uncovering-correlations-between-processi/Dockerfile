# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies (if any needed later, e.g., build tools)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY code/ ./code/
COPY docs/ ./docs/
COPY data/ ./data/
COPY tests/ ./tests/

# Create necessary data directories if they don't exist (in case of fresh run)
RUN mkdir -p data/raw data/processed figures

# Default command: run the main pipeline
# The ENABLE_DOCKER flag is expected to be set in the CI workflow or via docker run --build-arg
# If ENABLE_DOCKER is false, the entrypoint script handles the skip logic.
# However, standard Dockerfiles don't have conditional build steps for "skipping" execution
# based on an env var at runtime easily without an entrypoint script.
# We will provide an entrypoint script that checks the flag.

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
