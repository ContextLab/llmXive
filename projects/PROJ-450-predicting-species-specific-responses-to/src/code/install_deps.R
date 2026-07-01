#!/usr/bin/env Rscript
# T002: Initialize R 4.3+ project with renv and install dependencies
# This script initializes renv, installs required packages, and creates a lockfile.

# Suppress warnings during installation to keep logs clean
options(warn = -1)

# Load required packages (base only for setup)
if (!requireNamespace("renv", quietly = TRUE)) {
  install.packages("renv", repos = "https://cloud.r-project.org")
}
library(renv)

# Initialize renv in the project root (assuming this runs from project root)
# If running from src/code, we need to set the project root explicitly
project_root <- normalizePath("..", winslash = "/")
if (!file.exists(file.path(project_root, "renv.lock"))) {
  message("Initializing renv in project root: ", project_root)
  renv::init(path = project_root, force = TRUE)
} else {
  message("renv.lock already exists. Skipping initialization.")
}

# Define required packages
required_packages <- c(
  "rgbif",
  "raster",
  "sf",
  "ggplot2",
  "dplyr",
  "tidyr",
  "caper",
  "phylolm",
  "pwr",
  "tibble",
  "lubridate",
  "here",
  "testthat"
)

# Install packages if not already installed in the renv environment
message("Installing required packages...")
renv::install(required_packages, force = TRUE)

# Save the lockfile to ensure reproducibility
message("Saving renv lockfile...")
renv::snapshot(path = project_root, force = TRUE)

message("Dependency installation complete. Project is ready for T003 (Rprofile config).")
