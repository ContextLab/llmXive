# Dockerfile for PROJ-492: Evaluating the Statistical Validity of Public A/B Test Summaries
# Base image: CPU-compatible, lightweight, Python 3.11 slim
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies (if any needed for compilation)
# Currently none required beyond standard libs and pure Python wheels
# Uncomment if scipy/numpy require build tools in future
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY code/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source code
COPY code/src ./src
COPY code/data ./data
COPY code/tests ./tests
COPY code/scripts ./scripts
COPY code/specs ./specs
COPY code/contracts ./contracts
COPY code/config.py ./config.py
COPY code/setup_linting.py ./setup_linting.py
COPY code/setup_project_structure.py ./setup_project_structure.py

# Create necessary directories that might be empty but required at runtime
RUN mkdir -p data/raw data/manual_validation output figures

# Default command: run the main audit pipeline
# Users can override with docker run ... python scripts/<script>.py
ENTRYPOINT ["python", "scripts/run_audit.py"]

# Health check (optional, verifies basic import)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import sys; sys.path.insert(0, '.'); from src.audit.monte_carlo_core import set_seeds; print('OK')" || exit 1