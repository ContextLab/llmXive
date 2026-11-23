#!/bin/bash
# Script to install system dependencies for HISAT2, fastp, and featureCounts
# This script assumes a Debian/Ubuntu-based Linux environment.
# For other systems, use the appropriate package manager or build from source.

set -e

echo "Updating package lists..."
sudo apt-get update

echo "Installing common dependencies..."
sudo apt-get install -y \
    build-essential \
    cmake \
    wget \
    curl \
    git \
    libncurses5-dev \
    libncursesw5-dev \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    python3-dev \
    python3-pip

echo "Installing HISAT2..."
# HISAT2 installation
HISAT2_VERSION="2.2.1"
wget https://github.com/DaehwanKimLab/hisat2/releases/download/v${HISAT2_VERSION}/hisat2-${HISAT2_VERSION}-Linux_x86_64.zip
unzip hisat2-${HISAT2_VERSION}-Linux_x86_64.zip
sudo mv hisat2-${HISAT2_VERSION} /opt/hisat2
sudo ln -s /opt/hisat2/hisat2 /usr/local/bin/hisat2
sudo ln -s /opt/hisat2/hisat2-build /usr/local/bin/hisat2-build
sudo ln -s /opt/hisat2/hisat2-inspect /usr/local/bin/hisat2-inspect
rm -rf hisat2-${HISAT2_VERSION}*
echo "HISAT2 installed successfully."

echo "Installing fastp..."
# fastp installation
FASTP_VERSION="0.23.2"
wget https://github.com/OpenGene/fastp/releases/download/v${FASTP_VERSION}/fastp-${FASTP_VERSION}-linux.tar.gz
tar -xzf fastp-${FASTP_VERSION}-linux.tar.gz
sudo mv fastp-${FASTP_VERSION}-linux/fastp /usr/local/bin/
chmod +x /usr/local/bin/fastp
rm -rf fastp-${FASTP_VERSION}*
echo "fastp installed successfully."

echo "Installing featureCounts (from Subread package)..."
# featureCounts installation
SUBREAD_VERSION="2.0.3"
wget https://sourceforge.net/projects/subread/files/subread-${SUBREAD_VERSION}/subread-${SUBREAD_VERSION}-linux-x86_64.tar.gz
tar -xzf subread-${SUBREAD_VERSION}-linux-x86_64.tar.gz
sudo mv subread-${SUBREAD_VERSION}-linux-x86_64/bin/featureCounts /usr/local/bin/
sudo mv subread-${SUBREAD_VERSION}-linux-x86_64/bin/featureCounts /usr/local/bin/featureCounts
rm -rf subread-${SUBREAD_VERSION}*
echo "featureCounts installed successfully."

echo "Verifying installations..."
hisat2 --version
fastp --version
featureCounts --version

echo "All system dependencies installed successfully."
