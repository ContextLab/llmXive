# Dockerfile for PROJ-492: Evaluating the Statistical Validity of Public A/B Test Summaries
# CPU-compatible base image for local execution
# Builds an image that can run the audit pipeline without GPU dependencies

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY code/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source code
COPY code/src ./src
COPY code/tests ./tests
COPY code/data ./data
COPY code/contracts ./contracts
COPY code/specs ./specs
COPY code/docs ./docs
COPY code/notebooks ./notebooks
COPY code/input ./input
COPY code/output ./output
COPY code/setup_project_structure.py .
COPY code/setup_linting.py .

# Create necessary directories that may not exist in the repo
RUN mkdir -p /app/data/raw /app/data/synthetic /app/data/manual_validation /app/data/provenance

# Set up default environment
ENV PYTHONPATH=/app

# Default command: run the audit pipeline
# Can be overridden when running the container
CMD ["python", "-m", "code.src.cli.run_audit"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Label the image
LABEL org.opencontainers.image.title="A/B Test Audit Pipeline" \
    org.opencontainers.image.description="Evaluating statistical validity of public A/B test summaries" \
    org.opencontainers.image.source="https://github.com/example/ab-test-audit" \
    org.opencontainers.image.version="0.1.0" \
    org.opencontainers.image.licenses="MIT"