#!/usr/bin/env Rscript
# T002: Initialize R 4.3+ project with renv and install dependencies
# This script sets up the R environment, initializes renv, and installs
# all required packages for the project.

# Check R version
if (packageVersion("R") < "4.3.0") {
  stop("This project requires R version 4.3.0 or higher. Current version: ", 
       packageVersion("R"))
}

# Define required packages
required_packages <- c(
  "rgbif",      # GBIF data access
  "raster",     # Raster data handling
  "sf",         # Simple features for spatial data
  "ggplot2",    # Visualization
  "dplyr",      # Data manipulation
  "tidyr",      # Data tidying
  "caper",      # Comparative analyses
  "phylolm",    # Phylogenetic linear models
  "pwr",        # Power analysis
  "tibble",     # Tibble data frames
  "lubridate",  # Date/time handling
  "here",       # Project root handling
  "testthat"    # Testing framework
)

# Initialize renv if not already initialized
if (!dir.exists("renv")) {
  message("Initializing renv environment...")
  renv::init()
} else {
  message("renv environment already exists.")
}

# Install packages if not already installed
message("Checking and installing required packages...")
for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    message("Installing package: ", pkg)
    install.packages(pkg, dependencies = TRUE)
  } else {
    message("Package already installed: ", pkg)
  }
}

# Snapshot the environment to lock versions
message("Snapshotting renv environment...")
renv::snapshot()

message("R environment setup complete. All dependencies installed.")
