# Dockerfile for PMD/Java static analysis environment
FROM eclipse-temurin:17-jdk-alpine

# Install PMD CLI
# Using Alpine package manager for lightweight base
RUN apk add --no-cache \
    pmd \
    unzip \
    curl

# Verify Java installation
RUN java -version

# Verify PMD installation
RUN pmd --version

# Set working directory
WORKDIR /app

# Copy project files (excluding data and large artifacts)
COPY code/ ./code/
COPY data/intermediate/ ./data/intermediate/
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Default command
CMD ["sh"]
