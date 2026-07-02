# code/00_config.R
# Configuration management for the Chronotype-Moral Judgement study.
# Manages environment variables, file paths, and project constants.

# Define project root (assumes script runs from project root or RStudio project root)
# If run from a subdirectory, this logic attempts to find the root by looking for a known file.
get_project_root <- function() {
  # Try to find root by looking for 'data/raw' or 'README.md' in parent directories
  current <- getwd()
  search_path <- c(current, dirname(current), dirname(dirname(current)))
  
  for (dir in search_path) {
    if (file.exists(file.path(dir, "README.md")) || file.exists(file.path(dir, "data"))) {
      return(dir)
    }
  }
  # Fallback: assume current working directory is root
  return(current)
}

PROJECT_ROOT <- get_project_root()

# --- Directory Structure Constants ---
DIR_RAW <- file.path(PROJECT_ROOT, "data", "raw")
DIR_PROCESSED <- file.path(PROJECT_ROOT, "data", "processed")
DIR_DERIVED <- file.path(PROJECT_ROOT, "data", "derived")
DIR_LOGS <- file.path(PROJECT_ROOT, "logs")
DIR_CODE <- file.path(PROJECT_ROOT, "code")
DIR_REPORTS <- file.path(PROJECT_ROOT, "reports")

# Ensure directories exist
ensure_dirs <- function() {
  dirs <- c(DIR_RAW, DIR_PROCESSED, DIR_DERIVED, DIR_LOGS, DIR_REPORTS)
  for (d in dirs) {
    if (!dir.exists(d)) {
      dir.create(d, recursive = TRUE)
      message(sprintf("Created directory: %s", d))
    }
  }
}

# --- File Path Constants ---
# Input/Output files
FILE_CLEANED_DATA <- file.path(DIR_PROCESSED, "cleaned_data.csv")
FILE_CLASSIFIED_DATA <- file.path(DIR_DERIVED, "classified_data.csv")
FILE_ANCOVA_RESULTS <- file.path(DIR_DERIVED, "ancova_results.csv")
FILE_EFFECT_SIZES <- file.path(DIR_DERIVED, "effect_sizes.csv")
FILE_RELIABILITY_METRICS <- file.path(DIR_DERIVED, "reliability_metrics.csv")
FILE_SENSITIVITY_SWEEP <- file.path(DIR_DERIVED, "sensitivity_sweep.csv")

# Exclusion and Log files
FILE_INGEST_EXCLUSIONS_COUNT <- file.path(DIR_DERIVED, "ingest_exclusion_count.json")
FILE_CLASSIFY_EXCLUSIONS_LOG <- file.path(DIR_LOGS, "classify_exclusions.log")
FILE_INGEST_EXCLUSIONS_LOG <- file.path(DIR_LOGS, "ingest_exclusions.log")
FILE_EXCLUSIONS_LOG <- file.path(DIR_DERIVED, "exclusions.log")
FILE_EXCLUSION_COUNTS <- file.path(DIR_DERIVED, "exclusion_counts.json")
FILE_VIF_WARNING_LOG <- file.path(DIR_LOGS, "vif_warnings.log")
FILE_VIF_ERROR_FLAG <- file.path(DIR_LOGS, "vif_error.flag")

# --- Study Parameters (Constants from Spec) ---
# Chronotype Thresholds (MEQ)
MEQ_MORNING_THRESHOLD <- 59
MEQ_EVENING_THRESHOLD <- 41

# Statistical Parameters
ALPHA_BASE <- 0.05
NUM_SUBSCALES <- 5
ALPHA_CORRECTED <- ALPHA_BASE / NUM_SUBSCALES # Bonferroni
VIF_THRESHOLD <- 2.0
EXCLUSION_RATE_THRESHOLD <- 0.20

# --- Initialization ---
# Run directory creation immediately upon sourcing
ensure_dirs()

# --- Helper Functions ---

# Log message to a specific log file
log_message <- function(msg, log_file = NULL) {
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  formatted_msg <- sprintf("[%s] %s", timestamp, msg)
  message(formatted_msg) # Also print to console
  
  if (!is.null(log_file)) {
    if (!file.exists(log_file)) {
      file.create(log_file)
    }
    cat(formatted_msg, "\n", file = log_file, append = TRUE)
  }
}

# Abort helper with logging
abort_with_log <- function(msg, log_file = NULL) {
  log_message(paste("ABORT:", msg), log_file)
  stop(msg)
}

# Export all configuration symbols
config_env <- new.env()
assign("PROJECT_ROOT", PROJECT_ROOT, envir = config_env)
assign("DIR_RAW", DIR_RAW, envir = config_env)
assign("DIR_PROCESSED", DIR_PROCESSED, envir = config_env)
assign("DIR_DERIVED", DIR_DERIVED, envir = config_env)
assign("DIR_LOGS", DIR_LOGS, envir = config_env)
assign("DIR_CODE", DIR_CODE, envir = config_env)
assign("DIR_REPORTS", DIR_REPORTS, envir = config_env)
assign("FILE_CLEANED_DATA", FILE_CLEANED_DATA, envir = config_env)
assign("FILE_CLASSIFIED_DATA", FILE_CLASSIFIED_DATA, envir = config_env)
assign("FILE_ANCOVA_RESULTS", FILE_ANCOVA_RESULTS, envir = config_env)
assign("FILE_EFFECT_SIZES", FILE_EFFECT_SIZES, envir = config_env)
assign("FILE_RELIABILITY_METRICS", FILE_RELIABILITY_METRICS, envir = config_env)
assign("FILE_SENSITIVITY_SWEEP", FILE_SENSITIVITY_SWEEP, envir = config_env)
assign("FILE_INGEST_EXCLUSIONS_COUNT", FILE_INGEST_EXCLUSIONS_COUNT, envir = config_env)
assign("FILE_CLASSIFY_EXCLUSIONS_LOG", FILE_CLASSIFY_EXCLUSIONS_LOG, envir = config_env)
assign("FILE_INGEST_EXCLUSIONS_LOG", FILE_INGEST_EXCLUSIONS_LOG, envir = config_env)
assign("FILE_EXCLUSIONS_LOG", FILE_EXCLUSIONS_LOG, envir = config_env)
assign("FILE_EXCLUSION_COUNTS", FILE_EXCLUSION_COUNTS, envir = config_env)
assign("FILE_VIF_WARNING_LOG", FILE_VIF_WARNING_LOG, envir = config_env)
assign("FILE_VIF_ERROR_FLAG", FILE_VIF_ERROR_FLAG, envir = config_env)
assign("MEQ_MORNING_THRESHOLD", MEQ_MORNING_THRESHOLD, envir = config_env)
assign("MEQ_EVENING_THRESHOLD", MEQ_EVENING_THRESHOLD, envir = config_env)
assign("ALPHA_BASE", ALPHA_BASE, envir = config_env)
assign("NUM_SUBSCALES", NUM_SUBSCALES, envir = config_env)
assign("ALPHA_CORRECTED", ALPHA_CORRECTED, envir = config_env)
assign("VIF_THRESHOLD", VIF_THRESHOLD, envir = config_env)
assign("EXCLUSION_RATE_THRESHOLD", EXCLUSION_RATE_THRESHOLD, envir = config_env)
assign("log_message", log_message, envir = config_env)
assign("abort_with_log", abort_with_log, envir = config_env)

# Make available globally if sourced
.GlobalEnv$CONFIG <- config_env