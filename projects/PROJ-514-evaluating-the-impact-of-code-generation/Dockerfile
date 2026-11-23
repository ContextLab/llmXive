# Dockerfile for Code Smell Analysis Pipeline
# This Dockerfile sets up the environment with PMD CLI and JRE for static analysis

FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Java (OpenJDK 17)
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    python3 \
    python3-pip \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Install PMD CLI
# Using PMD 7.0.0 (or latest stable)
RUN wget https://github.com/pmd/pmd/releases/download/pmd_releases%2F7.0.0/pmd-bin-7.0.0.tar.gz \
    && tar -xzf pmd-bin-7.0.0.tar.gz \
    && mv pmd-bin-7.0.0 /opt/pmd \
    && ln -s /opt/pmd/bin/pmd /usr/local/bin/pmd \
    && rm pmd-bin-7.0.0.tar.gz

# Set PMD_HOME
ENV PMD_HOME=/opt/pmd
ENV PATH=$PMD_HOME/bin:$PATH

# Create project directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY code/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy project code
COPY code/ ./code/
COPY tests/ ./tests/
COPY data/ ./data/
COPY specs/ ./specs/
COPY reports/ ./reports/

# Set up environment variables
ENV PYTHONPATH=/app

# Run environment check on build to ensure PMD is available
RUN python3 code/utils/pmd_env_check.py

# Default command: run the environment check
CMD ["python3", "code/utils/pmd_env_check.py"]
