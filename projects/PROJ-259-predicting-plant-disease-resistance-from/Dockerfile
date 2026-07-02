# Plant Disease Resistance Prediction Pipeline Dockerfile
# Base image: Python 3.11 slim for smaller footprint
FROM python:3.11-slim

# Metadata
LABEL maintainer="llmXive Research Team"
LABEL description="Pipeline for predicting plant disease resistance from multi-omics data"

# Set working directory
WORKDIR /app

# Install system dependencies required for bioinformatics tools
# fastp: Ultra-fast all-in-one FASTQ preprocessor
# bcftools: Tools for variant calling and manipulating VCF/BCF files
# wget/curl: Required for downloading tools and data
# gcc/g++: Required for compiling some Python dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    fastp \
    bcftools \
    wget \
    curl \
    gcc \
    g++ \
    libbz2-dev \
    liblzma-dev \
    && rm -rf /var/lib/apt/lists/*

# Verify installation of bioinformatics tools
RUN fastp --version && bcftools --version

# Copy requirements first for better Docker layer caching
# This ensures dependency installation only re-runs when requirements change
COPY requirements.txt .

# Upgrade pip and install Python dependencies
# Installing dependencies separately from code allows for caching
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project code
# Including code/, data/, tests/, and other project files
COPY . .

# Set environment variables
# PYTHONPATH ensures the code directory is importable
# This allows imports like 'from config import get_path' to work correctly
ENV PYTHONPATH=/app

# Set default command to run the main pipeline
# Users can override this with 'docker run ... python code/main.py --args'
CMD ["python", "code/main.py"]
