#!/usr/bin/env Rscript
# install_packages.R
# Task: T003 - Initialize R environment with Bioconductor packages
# This script installs the required Bioconductor packages for the PPI pipeline.

# Check if BiocManager is installed, if not install it
if (!requireNamespace("BiocManager", quietly = TRUE)) {
  install.packages("BiocManager", repos = "https://cloud.r-project.org")
}

# List of required Bioconductor packages
required_packages <- c(
  "DESeq2",
  "org.At.tair.db",
  "biomaRt",
  "sva",
  "GEOquery"
)

# Install packages if not already installed
for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    message(sprintf("Installing %s...", pkg))
    BiocManager::install(pkg, ask = FALSE, update = FALSE)
  } else {
    message(sprintf("%s is already installed.", pkg))
  }
}

message("All required Bioconductor packages are installed.")
