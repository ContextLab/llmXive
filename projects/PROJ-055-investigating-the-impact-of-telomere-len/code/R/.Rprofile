# R Profile for PROJ-055
# Configure linting and formatting defaults

# Set default CRAN mirror
options(repos = c(CRAN = "https://cloud.r-project.org"))

# Load lintr if available for session linting
if (requireNamespace("lintr", quietly = TRUE)) {
  lintr::lint_package()
}

# Set default options for reproducibility
set.seed(42)

# Configure phylolm options if available
if (requireNamespace("phylolm", quietly = TRUE)) {
  # Ensure consistent model fitting behavior
  phylolm::phylolm.default.control <- list()
}
