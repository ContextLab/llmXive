# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for RDKit and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libfreetype6-dev \
    libpng-dev \
    libblas-dev \
    liblapack-dev \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd -m -u 1000 researcher
USER researcher
WORKDIR /home/researcher

# Copy requirements first for better caching
COPY --chown=researcher:researcher requirements.txt .

# Install Python dependencies with CPU-only PyTorch
# Note: --extra-index-url is required for torch cpu builds
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu \
        torch==2.2.0+cpu \
        scikit-learn==1.5.0 \
        rdkit==2024.3.1 \
        statsmodels==0.14.1 \
        pandas==2.2.0 \
        numpy==1.26.0 \
        matplotlib==3.8.0 \
        pyyaml==6.0.1 \
        requests==2.31.0

# Verify CPU-only enforcement (no CUDA libraries should be present)
# This step ensures the container does not accidentally pull GPU dependencies
RUN python -c "import torch; assert not torch.cuda.is_available(), 'GPU detected: CUDA is available but should be disabled'; print('CUDA disabled successfully')"

# Copy project source code
COPY --chown=researcher:researcher . .

# Default command
CMD ["bash"]