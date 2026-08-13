#!/bin/bash
# Setup script for R 4.3 dependencies
# This script installs required R packages if R is available.

set -e

echo "=== PROJ-002 R Environment Setup ==="

# Check if R is installed
if ! command -v R &> /dev/null; then
    echo "WARNING: R is not installed. Skipping R dependency installation."
    echo "Please install R 4.3+ and run this script manually or via the HPC environment."
    exit 0
fi

R_VERSION=$(R --version | head -n 1 | awk '{print $3}')
echo "Detected R version: $R_VERSION"

# Check major version
if [[ ! "$R_VERSION" =~ ^4\. ]]; then
    echo "WARNING: R 4.x is recommended. Current version: $R_VERSION"
fi

echo "Installing R dependencies..."

Rscript -e '
packages <- c("phylolm", "ape", "data.table", "ggplot2")
installed <- installed.packages()[, "Package"]
to_install <- setdiff(packages, installed)

if (length(to_install) > 0) {
    message("Installing: ", paste(to_install, collapse = ", "))
    install.packages(to_install, repos = "https://cloud.r-project.org")
    message("Installation complete.")
} else {
    message("All R dependencies already installed.")
}
'

echo "=== R Setup Complete ==="
