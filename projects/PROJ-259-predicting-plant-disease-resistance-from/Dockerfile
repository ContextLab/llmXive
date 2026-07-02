# =============================================================================
# Dockerfile for Predicting Plant Disease Resistance from Multi-omics Data
# =============================================================================
# This image provides the runtime environment for the llmXive pipeline.
# It includes Python 3.11, bioinformatics tools (fastp, bcftools),
# and all project Python dependencies.
# =============================================================================

# Use Python 3.11 slim base for a smaller footprint while retaining compatibility
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files and to
# ensure UTF-8 output for logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# ---------------------------------------------------------------------------
# Step 1: Install System Dependencies & Bioinformatics Tools
# ---------------------------------------------------------------------------
# We install build-essential for compiling Python packages, and specific
# bioinformatics tools required for preprocessing:
# - fastp: Ultra-fast all-in-one FASTQ preprocessor
# - bcftools: Tools for variant calling and manipulation
# We also add the EMBL-EBI repository to access up-to-date bio-tools.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    unzip \
    # Install bcftools (variant caller)
    bcftools \
    # Install fastp (sequencing preprocessor)
    fastp \
    # Clean up apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Step 2: Set Working Directory
# ---------------------------------------------------------------------------
# All subsequent commands will run inside this directory within the container.
WORKDIR /app

# ---------------------------------------------------------------------------
# Step 3: Copy and Install Python Dependencies
# ---------------------------------------------------------------------------
# We copy requirements.txt first to leverage Docker's layer caching.
# If the requirements file hasn't changed, pip install will be skipped
# in future builds, significantly speeding up the build process.
COPY code/requirements.txt ./requirements.txt

# Upgrade pip to latest version for security and compatibility, then install
# project dependencies. We use --no-cache-dir to keep the image size down.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Step 4: Copy Project Source Code
# ---------------------------------------------------------------------------
# Copy the entire project structure into the container.
# We exclude .git and other non-essential files via .dockerignore (assumed).
COPY . .

# ---------------------------------------------------------------------------
# Step 5: Create Necessary Directories
# ---------------------------------------------------------------------------
# Ensure that the output directories exist at runtime to prevent permission
# or existence errors when the pipeline tries to write logs or results.
RUN mkdir -p /app/data/raw /app/data/processed /app/artifacts/models \
    /app/artifacts/reports /app/artifacts/figures /app/tests

# ---------------------------------------------------------------------------
# Step 6: Default Command
# ---------------------------------------------------------------------------
# By default, the container will run the main pipeline entry point.
# Users can override this to run specific scripts or an interactive shell.
# Example override: docker run <image> python code/data/download.py
CMD ["python", "code/main.py"]