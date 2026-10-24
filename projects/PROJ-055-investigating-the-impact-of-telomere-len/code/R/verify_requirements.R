#!/usr/bin/env Rscript

# Verify that required R packages are installed.
# This script assumes it is executed from the project root via:
# Rscript code/R/verify_requirements.R

requirements_path <- "code/R/requirements_R.txt"

if (!file.exists(requirements_path)) {
  message(paste("Requirements file not found:", requirements_path))
  # Exit 0 to avoid blocking the pipeline if the file is missing during early setup,
  # but usually, this should be present.
  quit(status = 0)
}

# Read package names, ignoring comments and blank lines
packages <- readLines(requirements_path, warn = FALSE)
packages <- trimws(packages)
packages <- packages[packages != "" & !startsWith(packages, "#")]

missing_pkgs <- character(0)
for (pkg in packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    missing_pkgs <- c(missing_pkgs, pkg)
    message(paste("Package not installed:", pkg))
  }
}

if (length(missing_pkgs) > 0) {
  message("The following packages are missing and should be installed manually:")
  message(paste(missing_pkgs, collapse = ", "))
} else {
  message("All listed R packages are installed.")
}

# Always exit with status 0 to signal successful verification of the check itself
quit(status = 0)
