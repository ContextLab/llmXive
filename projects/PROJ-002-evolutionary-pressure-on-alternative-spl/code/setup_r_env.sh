#!/bin/bash
# Setup script to initialize the R environment for PROJ-002.
# Installs R packages from renv.lock.

set -e

RSCRIPT=$(which Rscript)
if [ -z "$RSCRIPT" ]; then
    echo "Error: Rscript not found. Please install R."
    exit 1
fi

echo "R version: $($RSCRIPT --version | head -n 1)"

RENV_LOCK="renv.lock"
if [ ! -f "$RENV_LOCK" ]; then
    echo "Error: $RENV_LOCK not found"
    exit 1
fi

echo "Installing R dependencies..."

# Install renv if not present
$RSCRIPT -e "if (!requireNamespace('renv', quietly = TRUE)) install.packages('renv', repos='https://cloud.r-project.org')"

# Restore environment from renv.lock
$RSCRIPT -e "renv::restore()"

echo "R environment setup complete."
