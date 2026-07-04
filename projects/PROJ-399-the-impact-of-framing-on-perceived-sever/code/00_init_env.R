#' Initialize Environment Configuration for PROJ-399
#'
#' This script sources the `.Renviron` file and sets up environment variables
#' required for the project. It acts as a bootstrap for all other R scripts.
#'
#' Usage: source("code/00_init_env.R")
#'
#' Dependencies: None (uses base R)

# Load environment variables from .Renenv if not already loaded
if (file.exists(".Renviron")) {
  readRenviron(".Renviron")
} else {
  stop("Environment file '.Renviron' not found in code/ directory. Please run T006.")
}

# Helper function to get env var with a fallback
get_env <- function(key, default = NULL) {
  val <- Sys.getenv(key, unset = NA)
  if (is.na(val)) {
    if (!is.null(default)) {
      return(default)
    } else {
      warning(sprintf("Environment variable '%s' is not set.", key))
      return(NA_character_)
    }
  }
  return(val)
}

# Validate critical paths exist or create them
validate_and_create_path <- function(path_var, name) {
  path <- get_env(path_var)
  if (is.na(path)) {
    stop(sprintf("Critical environment variable %s is not set.", path_var))
  }
  
  # Resolve relative to project root if needed
  # We assume the working directory is the project root when running scripts
  # or we resolve relative to this script's location if run from code/
  if (!startsWith(path, "/") && !startsWith(path, "~")) {
    # Assume relative to project root (parent of code/)
    full_path <- file.path("..", path)
  } else {
    full_path <- path
  }

  # Normalize path
  full_path <- normalizePath(full_path, mustWork = FALSE)

  if (!dir.exists(full_path)) {
    message(sprintf("Creating directory: %s", full_path))
    dir.create(full_path, recursive = TRUE, showWarnings = FALSE)
  }
  return(full_path)
}

# Set global paths for the session
env_paths <- list(
  data_processed = validate_and_create_path("R_DATA_PROCESSED", "Processed Data"),
  data_raw = validate_and_create_path("R_DATA_RAW", "Raw Data"),
  results_plots = validate_and_create_path("R_RESULTS_PLOTS", "Results Plots"),
  results_intermediate = validate_and_create_path("R_RESULTS_INTERMEDIATE", "Intermediate Results"),
  results_processed = validate_and_create_path("R_RESULTS_PROCESSED", "Processed Results")
)

# Store paths in global environment for easy access
for (name in names(env_paths)) {
  assign(name, env_paths[[name]], envir = .GlobalEnv)
}

# Load config seed if available
config_path <- get_env("R_CONFIG_PATH")
if (!is.na(config_path)) {
  if (file.exists(config_path)) {
    message(sprintf("Loading configuration from: %s", config_path))
    # We will load this in utils.R or specific scripts using yaml package
    # For now, just verify it exists
  } else {
    warning(sprintf("Config file not found at: %s. Seed may not be set.", config_path))
  }
}

message("Environment initialization complete.")
message(sprintf("Data processed dir: %s", data_processed))
message(sprintf("Data raw dir: %s", data_raw))
message(sprintf("Results plots dir: %s", results_plots))
