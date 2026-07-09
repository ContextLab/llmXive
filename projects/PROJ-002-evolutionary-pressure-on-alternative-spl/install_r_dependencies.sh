#!/bin/bash
# Script to install R 4.3+ and required R packages for PROJ-002
# This script assumes R 4.3+ is installed or available via system package manager.
# If not, it attempts to install R from CRAN or system repos.

set -e

echo "=== Checking R installation ==="
if ! command -v R &> /dev/null; then
    echo "R not found. Attempting to install R 4.3+..."
    if [ -f /etc/os-release ]; then
        source /etc/os-release
        case "$ID" in
            ubuntu|debian)
                sudo apt-get update
                sudo apt-get install -y r-base r-base-dev
                ;;
            centos|rhel|fedora)
                sudo yum install -y R R-core R-core-devel
                ;;
            macos)
                echo "On macOS, please install R 4.3+ via Homebrew: brew install r"
                exit 1
                ;;
            *)
                echo "Unsupported OS: $ID. Please install R 4.3+ manually."
                exit 1
                ;;
        esac
    else
        echo "Cannot detect OS. Please install R 4.3+ manually."
        exit 1
    fi
fi

R_VERSION=$(R --version | head -n 1 | grep -oP '\d+\.\d+\.\d+')
echo "Detected R version: $R_VERSION"

# Check minimum version
if [[ ! "$R_VERSION" =~ ^4\.[3-9]\. ]] && [[ ! "$R_VERSION" =~ ^[5-9]\. ]]; then
    echo "ERROR: R version $R_VERSION is too old. Requires R 4.3 or newer."
    exit 1
fi

echo "=== Installing R packages ==="
Rscript -e '
if (!requireNamespace("installr", quietly = TRUE)) {
    install.packages("installr", repos="https://cloud.r-project.org")
}
if (Sys.info()[["sysname"]] == "Linux") {
    if (!requireNamespace("remotes", quietly = TRUE)) {
        install.packages("remotes", repos="https://cloud.r-project.org")
    }
    # Install phylolm from CRAN
    if (!requireNamespace("phylolm", quietly = TRUE)) {
        install.packages("phylolm", repos="https://cloud.r-project.org")
    }
    # Install ape from CRAN
    if (!requireNamespace("ape", quietly = TRUE)) {
        install.packages("ape", repos="https://cloud.r-project.org")
    }
    # Install data.table from CRAN
    if (!requireNamespace("data.table", quietly = TRUE)) {
        install.packages("data.table", repos="https://cloud.r-project.org")
    }
    # Install ggplot2 from CRAN
    if (!requireNamespace("ggplot2", quietly = TRUE)) {
        install.packages("ggplot2", repos="https://cloud.r-project.org")
    }
} else if (Sys.info()[["sysname"]] == "Darwin") {
    # macOS: try binary installation
    if (!requireNamespace("phylolm", quietly = TRUE)) {
        install.packages("phylolm", repos="https://cloud.r-project.org")
    }
    if (!requireNamespace("ape", quietly = TRUE)) {
        install.packages("ape", repos="https://cloud.r-project.org")
    }
    if (!requireNamespace("data.table", quietly = TRUE)) {
        install.packages("data.table", repos="https://cloud.r-project.org")
    }
    if (!requireNamespace("ggplot2", quietly = TRUE)) {
        install.packages("ggplot2", repos="https://cloud.r-project.org")
    }
}

# Verify installations
packages <- c("phylolm", "ape", "data.table", "ggplot2")
missing <- packages[!sapply(packages, requireNamespace, quietly = TRUE)]
if (length(missing) > 0) {
    stop(paste("Failed to install R packages:", paste(missing, collapse = ", ")))
}
cat("All required R packages installed successfully.\n")
'

echo "=== R environment setup complete ==="
