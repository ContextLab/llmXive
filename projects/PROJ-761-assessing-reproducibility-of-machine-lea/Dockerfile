# syntax=docker/dockerfile:1
# Dockerfile for PROJ-761: Assessing Reproducibility of Machine-Learned Reaction Yield Models
# Enforces CPU-only execution, Python 3.11, and specific library versions.

# Base image: Python 3.11 slim
FROM python:3.11-slim

# Set environment variables to enforce CPU-only behavior and disable GPU detection
ENV NVIDIA_VISIBLE_DEVICES=""
ENV CUDA_VISIBLE_DEVICES=""
ENV TORCH_CUDA_ARCH_LIST=""
ENV PYTORCH_NO_CUDA=1

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies required for RDKit and other scientific libraries
# Build-essential for compiling some packages, git for fetching, and libgomp for OpenMP
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libgomp1 \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
# Note: PyTorch CPU-only version is specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy project source code
COPY code/ ./code/
COPY data/ ./data/
COPY contracts/ ./contracts/
COPY tests/ ./tests/
COPY artifacts/ ./artifacts/
COPY specs/ ./specs/
COPY README.md .
COPY pyproject.toml .

# Create necessary directories if they don't exist (redundant but safe)
RUN mkdir -p data/raw data/processed artifacts/logs artifacts/plots artifacts/reports

# Default command: run the main pipeline
# This can be overridden by the user or CI/CD
CMD ["python", "code/main.py"]