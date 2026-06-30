# syntax=docker/dockerfile:1
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies required for nibabel, nilearn, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libhdf5-dev \
    libblas-dev \
    liblapack-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source code
COPY code/ ./code/
COPY tests/ ./tests/
COPY specs/ ./specs/
COPY data/ ./data/
COPY README.md .
COPY tasks.md .

# Create necessary directories if they don't exist (robustness)
RUN mkdir -p data/raw/behavioral data/processed data/results data/logs figures

# Set the entrypoint to python, allowing arguments to be passed
# Example: docker run -it <image> python code/main.py
ENTRYPOINT ["python"]

# Default command (can be overridden)
CMD ["code/main.py"]
