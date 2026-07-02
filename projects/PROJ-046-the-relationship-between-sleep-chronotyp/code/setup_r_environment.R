#!/usr/bin/env Rscript
# setup_r_environment.R
# Initialize R 4.3+ project with renv and required dependencies.
# This script ensures the project uses a consistent R environment
# and installs all required packages.

# Load required libraries (base R only for setup)
if (!requireNamespace("renv", quietly = TRUE)) {
  install.packages("renv", repos = "https://cloud.r-project.org")
}

library(renv)

# Define required packages
required_packages <- c(
  "tidyverse",
  "lme4",
  "car",
  "effectsize",
  "pwr",
  "rmarkdown",
  "knitr",
  "data.table",
  "testthat",
  "lintr"
)

# Initialize renv if not already initialized
if (!file.exists("renv.lock")) {
  message("Initializing renv environment...")
  renv::init(bare = TRUE)
} else {
  message("renv environment already exists. Loading...")
  renv::load()
}

# Install missing packages
installed_packages <- rownames(installed.packages())
missing_packages <- setdiff(required_packages, installed_packages)

if (length(missing_packages) > 0) {
  message(paste("Installing missing packages:", paste(missing_packages, collapse = ", ")))
  renv::install(missing_packages)
} else {
  message("All required packages are already installed.")
}

# Verify installation
message("Verifying package installations...")
for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    stop(paste("Failed to load required package:", pkg))
  }
  message(paste("✓", pkg, "is available"))
}

message("R environment setup complete.")
