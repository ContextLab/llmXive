# syntax=docker/dockerfile:1
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install JRE (required for PMD) and git
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-11-jre-headless \
    git \
    curl \
    unzip \
&& rm -rf /var/lib/apt/lists/*

# Set PMD version
ARG PMD_VERSION=7.0.0
ARG PMD_BASE_URL=https://github.com/pmd/pmd/releases/download

# Download and install PMD CLI
RUN curl -fsSL "${PMD_BASE_URL}/pmd_releases/${PMD_VERSION}/pmd-bin-${PMD_VERSION}.zip" -o /tmp/pmd.zip \
    && unzip /tmp/pmd.zip -d /opt/ \
    && ln -s /opt/pmd-bin-${PMD_VERSION}/bin/pmd /usr/local/bin/pmd \
    && rm /tmp/pmd.zip

# Verify installation
RUN pmd --version

# Set environment variables for PMD
ENV PMD_HOME=/opt/pmd-bin-${PMD_VERSION}
ENV PATH="${PMD_HOME}/bin:${PATH}"

# Create a non-root user for running analysis
RUN useradd -m -s /bin/bash analyst
USER analyst

# Default command to verify environment
CMD ["pmd", "check", "--help"]
