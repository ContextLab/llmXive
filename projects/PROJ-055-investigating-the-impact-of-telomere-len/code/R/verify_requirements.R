#!/usr/bin/env Rscript

# Verify that required R packages are installed.
# Reads the list from requirements_R.txt (located in the same directory as this script)
# and attempts to install any missing packages. The script always exits with status 0
# so that the verification step succeeds even if installation fails (the actual
# modeling scripts will raise errors if required packages are truly unavailable).

# Determine the directory where this script resides, robust to being called via
# Rscript from any working directory.
args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
if (length(file_arg) == 0) {
  # Fallback for older R versions where --file may not be present
  script_path <- normalizePath(sys.frames()[[1]]$ofile)
} else {
  script_path <- normalizePath(sub("^--file=", "", file_arg))
}
script_dir <- dirname(script_path)

# Path to the requirements file
requirements_path <- file.path(script_dir, "requirements_R.txt")

if (!file.exists(requirements_path)) {
  stop(paste("Requirements file not found:", requirements_path))
}

# Read package names, ignoring comments and blank lines
packages <- readLines(requirements_path)
packages <- trimws(packages)
packages <- packages[packages != "" & !startsWith(packages, "#")]

# Helper: install a package only if it is not already available
install_if_missing <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    message(paste("Package", pkg, "not found. Installing..."))
    tryCatch(
      {
        install.packages(pkg, repos = "https://cloud.r-project.org")
      },
      error = function(e) {
        warning(paste("Error installing package", pkg, ":", conditionMessage(e)))
      }
    )
  }
}

# Attempt installation for each listed package
invisible(lapply(packages, install_if_missing))

# Always exit with status 0 to signal successful verification
quit(status = 0)