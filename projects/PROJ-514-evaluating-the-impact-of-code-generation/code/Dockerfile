FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update package lists and install prerequisites
# Includes OpenJDK 17 (required for PMD) and basic build tools
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk-headless \
    wget \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Verify Java installation
RUN java -version

# Download and install PMD CLI
# Using a stable, recent version (6.55.0)
RUN wget -q https://github.com/pmd/pmd/releases/download/pmd_releases%2F6.55.0/pmd-bin-6.55.0.zip -O /tmp/pmd-bin.zip \
    && unzip -q /tmp/pmd-bin.zip -d /opt \
    && rm /tmp/pmd-bin.zip \
    && ln -s /opt/pmd-bin-6.55.0/bin/pmd /usr/local/bin/pmd

# Verify PMD installation
RUN pmd --version

# Set working directory
WORKDIR /workspace

# Default command to verify environment
CMD ["bash", "-c", "java -version && pmd --version && echo 'PMD and JRE ready for CI checks.'"]
