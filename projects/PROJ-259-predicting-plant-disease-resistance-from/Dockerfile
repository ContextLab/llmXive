# ==========================================
# Build Stage: Prepare Python Environment
# ==========================================
# Use official Python 3.11 slim image as base for smaller footprint
FROM python:3.11-slim as builder

# Set environment variables to prevent Python from writing .pyc files
# and to ensure UTF-8 encoding for consistent behavior across locales
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create a non-root user for security best practices
# This user will run the application inside the container
RUN useradd --create-home --shell /bin/bash appuser

# ==========================================
# Build Stage: Install System Dependencies
# ==========================================
# Install bioinformatics tools required for preprocessing:
# - fastp: Ultra-fast all-in-one FASTQ preprocessor
# - bcftools: Tools for variant calling and manipulation
# Note: These are installed at the system level as they require low-level libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    fastp \
    bcftools \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ==========================================
# Build Stage: Install Python Dependencies
# ==========================================
# Create a virtual environment to isolate project dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements first to leverage Docker layer caching
# If requirements.txt hasn't changed, this layer is reused
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ==========================================
# Final Stage: Production Image
# ==========================================
# Start a new, smaller stage for the final image to reduce size
FROM python:3.11-slim

# Re-apply environment variables from builder stage
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH"

# Install runtime system dependencies (bioinformatics tools again)
# These are needed for the application to execute preprocessing steps
RUN apt-get update && apt-get install -y --no-install-recommends \
    fastp \
    bcftools \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for running the application
RUN useradd --create-home --shell /bin/bash appuser

# Create necessary directories for the application
# These match the directory structure created by T001
RUN mkdir -p /app/code /app/data /app/data/raw /app/data/processed \
        /app/artifacts /app/artifacts/models /app/artifacts/reports \
        /app/artifacts/figures /app/tests /app/specs && \
    chown -R appuser:appuser /app

# Switch to non-root user for security
USER appuser

# Set the working directory inside the container
WORKDIR /app

# Copy project source code and configuration
# This includes the Python modules, scripts, and config files
COPY --chown=appuser:appuser . .

# Copy the virtual environment from builder stage to avoid rebuilding dependencies
COPY --from=builder /opt/venv /opt/venv

# ==========================================
# Runtime Configuration
# ==========================================
# Set default environment variables for the application
# These can be overridden by the user at runtime via docker run -e
ENV PYTHONPATH=/app \
    DATA_DIR=/app/data \
    ARTIFACTS_DIR=/app/artifacts \
    LOG_LEVEL=INFO

# Expose any ports if the project includes a web service
# (Currently not required for this CLI pipeline, but reserved for future use)
# EXPOSE 8000

# Default command: Run the main pipeline entry point
# This can be overridden when running the container: docker run <image> python code/other_script.py
CMD ["python", "code/main.py"]