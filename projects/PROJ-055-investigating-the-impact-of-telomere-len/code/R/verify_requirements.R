#!/usr/bin/env Rscript

# Verify that required R packages are installed.
# This script assumes it is executed from the project root via:
# Rscript code/R/verify_requirements.R

requirements_path <- "code/R/requirements_R.txt"

if (!file.exists(requirements_path)) {
  message(paste("Requirements file not found:", requirements_path))
  quit(status = 1)
}

# Read package names, ignoring comments and blank lines
lines <- readLines(requirements_path, warn = FALSE)
lines <- trimws(lines)
lines <- lines[lines != "" & !startsWith(lines, "#")]

# Strip version numbers if present (e.g., "lme4==1.1-33" -> "lme4")
packages <- gsub("==.*", "", lines)

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
  quit(status = 1)
} else {
  message("All listed R packages are installed.")
  quit(status = 0)
}
