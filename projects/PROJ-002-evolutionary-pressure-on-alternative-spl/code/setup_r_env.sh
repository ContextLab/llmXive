#!/bin/bash
# R Environment Setup Script for PROJ-002
# Validates R version and installs required packages.

set -e

REQUIRED_R_VERSION="4.3"

echo "=== PROJ-002 R Environment Setup ==="

# Check R version
if ! command -v R &> /dev/null; then
    echo "Error: R is not installed. Please install R 4.3+."
    exit 1
fi

R_VERSION=$(R --version | grep "R version" | awk '{print $3}' | cut -d'.' -f1,2)
echo "Found R version: $R_VERSION"

# Simple version check (assuming 4.3.x)
if [[ ! "$R_VERSION" =~ ^4\.[0-9]+$ ]]; then
    echo "Warning: R version $R_VERSION detected. Expected 4.3.x. Proceeding anyway."
fi

# Install R packages
R_SCRIPT=$(mktemp)
cat > "$R_SCRIPT" << 'EOF'
# Install packages if not present
packages <- c("phylolm", "ape", "data.table", "ggplot2")
install.packages(packages, repos = "https://cloud.r-project.org")
library(phylolm)
library(ape)
library(data.table)
library(ggplot2)
cat("✓ All R packages installed and loaded successfully.\n")
EOF

echo "Installing R packages..."
R --vanilla --slave < "$R_SCRIPT"
rm "$R_SCRIPT"

echo "=== R Setup Complete ==="
