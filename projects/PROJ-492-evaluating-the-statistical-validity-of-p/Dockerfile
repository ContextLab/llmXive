# Use a CPU-compatible base image (Debian slim with Python 3.11)
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files and to buffer output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/code

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for any compiled extensions)
# Using build-essential and curl for potential runtime needs, though primarily CPU-only
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
# Copy requirements first to leverage Docker cache
COPY code/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the codebase
COPY code/ ./code/
COPY data/ ./data/
COPY contracts/ ./contracts/
COPY tests/ ./tests/
COPY docs/ ./docs/
COPY specs/ ./specs/

# Create necessary output directories
RUN mkdir -p output/ figures/ data/raw/ data/manual_validation/

# Set the default command to run a simple help check or the main CLI
# The actual audit run would be invoked via docker run ... python code/src/cli/run_audit.py
ENTRYPOINT ["python", "code/src/cli/main.py"]
CMD ["--help"]