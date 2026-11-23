#!/usr/bin/env Rscript

# Install R packages listed in requirements_R.txt
requirements_path <- "code/R/requirements_R.txt"

if (!file.exists(requirements_path)) {
  stop(paste("Requirements file not found:", requirements_path))
}

lines <- readLines(requirements_path, warn = FALSE)
lines <- trimws(lines)
lines <- lines[lines != "" & !startsWith(lines, "#")]
packages <- gsub("==.*", "", lines)

message("Installing R packages: ", paste(packages, collapse = ", "))
install.packages(packages, repos = "https://cloud.r-project.org")
message("R package installation complete.")
