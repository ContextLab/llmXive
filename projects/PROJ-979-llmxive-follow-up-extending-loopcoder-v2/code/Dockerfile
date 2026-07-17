# Docker sandbox for safe code execution in llmXive pipeline
# Based on minimal Python image with restricted permissions

FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install minimal dependencies for code execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 sandbox
USER sandbox
WORKDIR /home/sandbox

# Create directories for execution and logs
RUN mkdir -p /home/sandbox/exec /home/sandbox/logs /home/sandbox/output
RUN chmod 755 /home/sandbox/exec /home/sandbox/logs /home/sandbox/output

# Install runtime dependencies (minimal)
# Note: Heavy packages like numpy/pandas should be installed if needed
# For now, we provide a minimal Python environment
RUN pip install --no-cache-dir --upgrade pip

# Copy execution script
COPY --chown=sandbox:sandbox scripts/execute.py /home/sandbox/

# Set entrypoint to execution script
ENTRYPOINT ["python", "execute.py"]
