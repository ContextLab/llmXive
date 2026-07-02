# ============================================================================
# Dockerfile for llmXive: Predicting Plant Disease Resistance from Multi-omics Data
# ============================================================================
# This container provides the runtime environment for the research pipeline.
# It includes Python 3.11, bioinformatics tools (fastp, bcftools), and
# project-specific Python dependencies.
# ============================================================================

# Use official Python 3.11 slim image as base for smaller size and stability
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files
# and to ensure UTF-8 encoding for file operations and logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Set the working directory inside the container
# All subsequent commands will run relative to this path
WORKDIR /app

# --------------------------------------------------------------------------
# Step 1: Install System Dependencies
# --------------------------------------------------------------------------
# Update package lists to ensure we get the latest versions of tools.
# Install build-essential for compiling any Python C extensions if needed.
# Install fastp for high-performance FASTQ preprocessing (adapter trimming, quality filtering).
# Install bcftools for variant calling and manipulation of VCF/BCF files.
# Install libbz2-dev and liblzma-dev for compression support in bioinformatics tools.
# Install curl and wget for downloading data files within the container.
# Install git for cloning repositories if needed during development.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    fastp \
    bcftools \
    libbz2-dev \
    liblzma-dev \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# --------------------------------------------------------------------------
# Step 2: Install Python Dependencies
# --------------------------------------------------------------------------
# Copy the requirements file first to leverage Docker layer caching.
# If requirements.txt hasn't changed, this step uses the cached layer.
COPY requirements.txt .

# Upgrade pip to the latest version to ensure compatibility with wheels.
# Install all Python dependencies listed in requirements.txt.
# --no-cache-dir ensures the pip cache isn't stored in the image, reducing size.
RUN pip install --no-cache-dir -r requirements.txt

# --------------------------------------------------------------------------
# Step 3: Copy Project Source Code
# --------------------------------------------------------------------------
# Copy the entire project source code into the container.
# This includes code/, data/, tests/, and configuration files.
# We copy everything to ensure the project structure is preserved.
COPY . .

# --------------------------------------------------------------------------
# Step 4: Create Non-Root User (Security Best Practice)
# --------------------------------------------------------------------------
# Create a non-root user 'researcher' to run the pipeline.
# Running as root is a security risk; this minimizes potential damage.
RUN useradd -m -u 1000 researcher

# Change ownership of the application directory to the new user.
# This ensures the 'researcher' user can read/write necessary files.
RUN chown -R researcher:researcher /app

# Switch to the non-root user for all subsequent commands.
USER researcher

# --------------------------------------------------------------------------
# Step 5: Define Default Command
# --------------------------------------------------------------------------
# Set the default command to run the main pipeline script.
# This can be overridden by the user when running the container.
# Example: docker run --rm llmXive python code/main.py --help
CMD ["python", "code/main.py"]