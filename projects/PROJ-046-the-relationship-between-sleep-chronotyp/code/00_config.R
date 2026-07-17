# code/00_config.R
# Configuration management for the pipeline

# Define project root relative to this file
get_project_root <- function() {
  current_dir <- dirname(sys.frame(1)$ofile)
  if (is.null(current_dir)) {
    current_dir <- getwd()
  }
  # Look for tasks.md in current or parent directories
  root <- current_dir
  while (!file.exists(file.path(root, "tasks.md"))) {
    parent <- dirname(root)
    if (parent == root) break
    root <- parent
  }
  return(root)
}

# Set paths
PROJECT_ROOT <- get_project_root()
DATA_DIR <- file.path(PROJECT_ROOT, "data")
RAW_DATA_DIR <- file.path(DATA_DIR, "raw")
PROCESSED_DATA_DIR <- file.path(DATA_DIR, "processed")
DERIVED_DATA_DIR <- file.path(DATA_DIR, "derived")
LOGS_DIR <- file.path(PROJECT_ROOT, "logs")
REPORTS_DIR <- file.path(PROJECT_ROOT, "reports")

# Ensure directories exist
ensure_directories <- function() {
  dirs <- c(DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, DERIVED_DATA_DIR, LOGS_DIR, REPORTS_DIR)
  for (d in dirs) {
    if (!dir.exists(d)) {
      dir.create(d, recursive = TRUE)
    }
  }
}

# Initialize config
ensure_directories()
