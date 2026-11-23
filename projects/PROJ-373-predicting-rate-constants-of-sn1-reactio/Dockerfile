# syntax=docker/dockerfile:1
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies required for RDKit and other packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project code and data schemas
COPY code/ ./code/
COPY data/ ./data/
COPY specs/ ./specs/
COPY tests/ ./tests/
COPY artifacts/ ./artifacts/
COPY *.md .
COPY *.ini .
COPY *.yaml .

# Create necessary directories if they don't exist (in case they are in .gitignore)
RUN mkdir -p data/raw data/processed artifacts figures

# Default command: run the main pipeline
# Note: This can be overridden at runtime with docker run <image> <command>
CMD ["python", "code/main.py"]
