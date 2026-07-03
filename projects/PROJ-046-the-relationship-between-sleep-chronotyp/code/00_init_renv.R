#!/usr/bin/env Rscript
# T002: Initialize R 4.3+ project with renv and dependencies
# This script sets up the R environment, initializes renv, and installs required packages.

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

# Check R version
r_version <- as.numeric(R.version$major) + as.numeric(R.version$minor) / 10
if (r_version < 4.3) {
  stop("This project requires R version 4.3 or higher. Current version: ", 
       R.version$major, ".", R.version$minor)
}

message("R version check passed: ", R.version$major, ".", R.version$minor)

# Initialize renv if not already initialized
if (!dir.exists("renv")) {
  message("Initializing renv...")
  renv::init()
} else {
  message("renv already initialized.")
}

# Install missing packages
installed_packages <- rownames(installed.packages())
missing_packages <- setdiff(required_packages, installed_packages)

if (length(missing_packages) > 0) {
  message("Installing missing packages: ", paste(missing_packages, collapse = ", "))
  renv::install(missing_packages)
} else {
  message("All required packages are already installed.")
}

# Snapshot the environment to create/update renv.lock
message("Snapshotting environment to create renv.lock...")
renv::snapshot()

message("R project initialization complete.")
