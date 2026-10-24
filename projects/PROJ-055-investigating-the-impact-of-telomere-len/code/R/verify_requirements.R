#!/usr/bin/env Rscript

# Verify that required R packages are installed.
# Reads the list from requirements_R.txt and attempts to install any missing packages.

# Determine the path to the requirements file relative to the project root.
# The script is invoked from the project root, so we can construct the path directly.
requirements_path <- file.path("code", "R", "requirements_R.txt")

if (!file.exists(requirements_path)) {
  stop(paste("Requirements file not found:", requirements_path))
}

packages <- readLines(requirements_path)
packages <- trimws(packages)
packages <- packages[packages != "" & !startsWith(packages, "#")]

install_if_missing <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    message(paste("Package", pkg, "not found. Installing..."))
    # Try to install; capture any error but do not abort the whole script.
    tryCatch(
      {
        install.packages(pkg, repos = "https://cloud.r-project.org")
        if (!requireNamespace(pkg, quietly = TRUE)) {
          warning(paste("Failed to install package:", pkg))
        }
      },
      error = function(e) {
        warning(paste("Error installing package", pkg, ":", conditionMessage(e)))
      }
    )
  }
}

invisible(lapply(packages, install_if_missing))

# If we reach here, the script has completed (whether packages were already present
# or installation attempts were made). Exit with status 0 to indicate success.
quit(status = 0)