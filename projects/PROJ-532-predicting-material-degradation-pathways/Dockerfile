FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY code/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY code/ ./code/
COPY tests/ ./tests/

# Set environment variables
ENV PYTHONPATH=/app

# Default command (can be overridden by docker-compose)
CMD ["python", "code/ingestion.py"]
