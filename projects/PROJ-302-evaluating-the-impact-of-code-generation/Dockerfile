# syntax=docker/dockerfile:1
# llmXive - Evaluating the Impact of Code Generation on Code Review Time
# CPU-only environment for data acquisition, feature extraction, and analysis

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies required for some Python packages (e.g., git, gcc for building extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source code
COPY code/ ./code/
COPY data/ ./data/
COPY tests/ ./tests/
COPY specs/ ./specs/

# Create necessary directories if they don't exist (handles cases where data/processed might be empty)
RUN mkdir -p data/raw data/processed figures docs

# Default command: run a simple validation or enter shell
# Users can override this to run specific scripts, e.g., `python code/data_acquisition/github_scraper.py`
CMD ["python", "-c", "import code; print('llmXive environment ready.')]
