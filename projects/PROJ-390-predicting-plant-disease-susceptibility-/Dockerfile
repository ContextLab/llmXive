FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including minimap2 and bcftools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    wget \
    curl \
    git \
    minimap2 \
    bcftools \
    libhdf5-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create virtual environment
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

CMD ["bash"]
