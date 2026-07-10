# Dockerfile for PROJ-492: Evaluating Statistical Validity of Public A/B Test Summaries
# Uses a CPU-compatible base image. No GPU support required.
# Build: docker build -t proj492-ab-audit .
# Run: docker run --rm proj492-ab-audit python code/src/cli/run_audit.py --help

FROM python:3.10-slim

# Set environment variables to prevent interactive prompts and ensure UTF-8
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Set working directory inside the container
WORKDIR /app

# Install system dependencies (if any specific to the project are needed later)
# Currently minimal, but kept for potential future use (e.g., compiling some libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY code/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project source code
COPY code/ .

# Create necessary directories if they don't exist (though they should be in the repo)
RUN mkdir -p data/raw data/manual_validation output figures

# Default command: Verify installation and show help
# This ensures the container runs successfully on startup without crashing immediately
CMD ["python", "code/src/cli/run_audit.py", "--help"]
