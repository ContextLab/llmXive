# Stage 1: Base image with Python 3.11 and system dependencies
FROM python:3.11-slim-bookworm AS base

# Install system dependencies required for bioinformatics tools and compilation
# fastp: Ultra-fast all-in-one FASTQ preprocessor
# bcftools: Utilities for variant calling and manipulation (requires htslib)
# gcc, make, libcurl4-openssl-dev, libbz2-dev, liblzma-dev: Build tools for compiling tools from source if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    fastp \
    bcftools \
    tabix \
    build-essential \
    libcurl4-openssl-dev \
    libbz2-dev \
    liblzma-dev \
    libhts-dev \
    git \
    curl \
&& rm -rf /var/lib/apt/lists/*

# Set working directory inside the container
WORKDIR /app

# Stage 2: Python environment setup
FROM base AS python-setup

# Copy only requirements first to leverage Docker layer caching
# This ensures we only reinstall dependencies if requirements.txt changes
COPY requirements.txt .

# Upgrade pip and install Python dependencies
# Dependencies include: pandas, numpy, scikit-learn, statsmodels, pyyaml, requests
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 3: Final production image
FROM base AS production

# Copy the Python environment and dependencies from the python-setup stage
# This avoids rebuilding the entire environment if only source code changes
COPY --from=python-setup /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-setup /usr/local/bin /usr/local/bin

# Copy the project source code into the container
# Includes code/, data/, specs/, and other necessary project files
COPY . .

# Set environment variables for the application
# PYTHONUNBUFFERED ensures Python output is sent straight to terminal without buffering
# PYTHONDONTWRITEBYTECODE prevents .pyc files from being written to disk
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app

# Set the working directory
WORKDIR $APP_HOME

# Create necessary directories if they don't exist (redundant but safe)
# Ensures data/raw, data/processed, artifacts, etc. are present
RUN mkdir -p data/raw data/processed artifacts/models artifacts/reports artifacts/figures

# Default command: Run the main pipeline script
# This can be overridden by docker run command arguments
CMD ["python", "code/main.py"]
