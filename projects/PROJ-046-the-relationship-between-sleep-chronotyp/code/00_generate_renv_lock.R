# Script to initialize renv and generate renv.lock
# Dependencies: tidyverse, lme4, car, effectsize, pwr, rmarkdown, knitr, data.table, testthat, lintr

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

# Check if renv is installed
if (!requireNamespace("renv", quietly = TRUE)) {
  message("Installing renv package...")
  install.packages("renv", repos = "https://cloud.r-project.org")
}

# Initialize renv if not already initialized
if (!dir.exists("renv")) {
  message("Initializing renv environment...")
  renv::init()
}

# Install any missing packages
missing_packages <- setdiff(required_packages, names(renv::dependencies()))
if (length(missing_packages) > 0) {
  message("Installing missing packages: ", paste(missing_packages, collapse = ", "))
  renv::install(missing_packages)
}

# Snapshot to generate/refresh renv.lock
message("Generating renv.lock snapshot...")
renv::snapshot()

message("renv.lock generated successfully in the project root.")