#!/usr/bin/env Rscript

# Verify that required R packages are installed.
# Reads the list from requirements_R.txt and attempts to install any missing packages.

# Determine the path to the requirements file (same directory as this script)
script_dir <- dirname(normalizePath(sys.frame(1)$ofile))
requirements_path <- file.path(script_dir, "requirements_R.txt")

if (!file.exists(requirements_path)) {
  stop(paste("Requirements file not found:", requirements_path))
}

packages <- readLines(requirements_path)
packages <- trimws(packages)
packages <- packages[packages != "" & !startsWith(packages, "#")]

install_if_missing <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    message(paste("Package", pkg, "not found. Installing..."))
    install.packages(pkg, repos = "https://cloud.r-project.org")
    if (!requireNamespace(pkg, quietly = TRUE)) {
      stop(paste("Failed to install package:", pkg))
    }
  }
}

invisible(lapply(packages, install_if_missing))

# If we reach here, all packages are available
quit(status = 0)