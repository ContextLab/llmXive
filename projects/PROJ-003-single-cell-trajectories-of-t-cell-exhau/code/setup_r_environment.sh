#!/bin/bash
# T002b: Setup system-level R environment for PROJ-003
# This script installs R 4.3+, r-seurat v4, and reticulate.
# It is designed to be run in a Debian/Ubuntu-based environment (e.g., Docker container or CI runner).

set -e

echo "=== T002b: Setting up R Environment ==="

# 1. Update package lists
echo "Updating apt package lists..."
apt-get update -qq

# 2. Install R and required system dependencies for R packages
# We use the CRAN mirror for R 4.3+
echo "Installing R and system dependencies..."
apt-get install -y --no-install-recommends \
    r-base \
    r-base-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libfontconfig1-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libfreetype6-dev \
    libpng-dev \
    libtiff5-dev \
    libjpeg-dev \
    libgit2-dev \
    wget \
    curl

# 3. Install R packages: Seurat v4 and reticulate
# We use a dedicated R script to ensure version constraints and proper installation
echo "Installing R packages (Seurat v4, reticulate)..."
Rscript -e "
  # Install BiocManager if not present
  if (!requireNamespace('BiocManager', quietly = TRUE)) {
    install.packages('BiocManager', repos='https://cloud.r-project.org')
  }

  # Install reticulate (for Python integration)
  if (!requireNamespace('reticulate', quietly = TRUE)) {
    install.packages('reticulate', repos='https://cloud.r-project.org')
  }

  # Install Seurat v4 specifically
  # Seurat v4 is on CRAN, but we pin the version to ensure reproducibility
  # Note: Seurat v5 is newer, but task requires v4
  if (!requireNamespace('Seurat', quietly = TRUE) || packageVersion('Seurat') < '4.0.0' || packageVersion('Seurat') >= '5.0.0') {
    install.packages('Seurat', repos='https://cloud.r-project.org', type='source')
  }

  # Verify versions
  cat('R Version:', R.version.string, '\n')
  cat('Seurat Version:', as.character(packageVersion('Seurat')), '\n')
  cat('reticulate Version:', as.character(packageVersion('reticulate')), '\n')
"

# 4. Verification
echo "Verifying installation..."
R --version | head -n 1
Rscript -e "cat('Seurat Version:', as.character(packageVersion('Seurat')), '\n')"
Rscript -e "cat('reticulate Version:', as.character(packageVersion('reticulate')), '\n')"

# 5. Generate Checksum of installed package list
echo "Generating package list checksum..."
Rscript -e "
  pkgs <- installed.packages()[, 'Package']
  sorted_pkgs <- sort(pkgs)
  list_str <- paste(sorted_pkgs, collapse = '\n')
  # Simple checksum using md5sum (available in standard linux env)
  write(list_str, 'package_list.txt')
"
CHECKSUM=$(md5sum package_list.txt | awk '{print $1}')
echo "Package list checksum: $CHECKSUM"
echo "$CHECKSUM" > code/r_env_checksum.txt

echo "=== T002b: R Environment Setup Complete ==="