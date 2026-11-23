#!/usr/bin/env Rscript
#
# Data Source Note:
# This pipeline requires a user-provided merged CSV file at data/raw/merged_questionnaire_data.csv.
# The script will ABORT immediately if required columns are missing.
# DO NOT use synthetic or placeholder data for primary analysis.
#
# Task: T011 - Ingest and Clean Data
# Description: Load CSV, verify columns, handle missing acute_sleepiness, check exclusion rate.
#
# Dependencies:
# - T006 (code/00_config.R)
# - T007 (code/utils_validation.R)
# - T008 (code/utils_logging.R)
#

# Load configuration and utilities
source("code/00_config.R")
source("code/utils_validation.R")
source("code/utils_logging.R")

# Main execution
main <- function() {
  # Initialize logger
  logger <- get_pipeline_logger()
  log_info(logger, "Starting data ingestion...")

  # Define paths
  input_path <- file.path(get_project_root(), "data", "raw", "merged_questionnaire_data.csv")
  output_path <- file.path(get_project_root(), "data", "processed", "cleaned_data.csv")
  exclusion_log_path <- file.path(get_project_root(), "logs", "ingest_exclusions.log")

  # Check if input file exists
  if (!file.exists(input_path)) {
    log_error(logger, "Input file not found: %s", input_path)
    log_abort(logger, "Pipeline aborted: Input file missing.")
    quit(status = 1)
  }

  # Load data
  log_info(logger, "Loading data from %s", input_path)
  tryCatch({
    raw_data <- read.csv(input_path, stringsAsFactors = FALSE)
  }, error = function(e) {
    log_error(logger, "Failed to load CSV: %s", e$message)
    log_abort(logger, "Pipeline aborted: Could not read input file.")
    quit(status = 1)
  })

  total_rows <- nrow(raw_data)
  log_info(logger, "Loaded %d rows", total_rows)

  # Define required columns
  required_cols <- c("MEQ_score", "MFQ_moral", "MFQ_utility", "MFQ_deontological", "MFQ_consequentialist", "MFQ_virtue", "PSQI", "acute_sleepiness", "age", "sex")

  # Verify presence of ALL required columns
  missing_cols <- setdiff(required_cols, colnames(raw_data))
  if (length(missing_cols) > 0) {
    log_error(logger, "Missing required columns: %s", paste(missing_cols, collapse = ", "))
    log_abort(logger, "Pipeline aborted: Missing required columns. Data source invalid.")
    quit(status = 1)
  }

  log_info(logger, "All required columns present.")

  # Initialize exclusion tracking
  exclusions <- data.frame(row_id = integer(), reason = character(), stringsAsFactors = FALSE)

  # Step 1: Check for missing acute_sleepiness
  missing_sleepiness <- is.na(raw_data$acute_sleepiness)
  if (any(missing_sleepiness)) {
    excluded_ids <- which(missing_sleepiness)
    exclusions <- rbind(exclusions, data.frame(row_id = excluded_ids, reason = "missing_acute_sleepiness", stringsAsFactors = FALSE))
    log_warning(logger, "Excluding %d rows due to missing acute_sleepiness", length(excluded_ids))
  }

  # Filter out missing acute_sleepiness
  cleaned_data <- raw_data[!missing_sleepiness, ]

  # Calculate exclusion rate
  current_excluded <- nrow(raw_data) - nrow(cleaned_data)
  exclusion_rate <- current_excluded / total_rows

  log_info(logger, "Exclusion rate after step 1: %.2f%%", exclusion_rate * 100)

  # IMMEDIATE ABORT CHECK: If exclusion rate > 20%, abort
  if (exclusion_rate > 0.20) {
    log_error(logger, "Exclusion rate (%.2f%%) exceeds 20%% threshold.", exclusion_rate * 100)
    log_abort(logger, "Pipeline aborted: Exclusion rate too high. No intermediate files saved.")
    quit(status = 1)
  }

  # Log exclusions
  if (nrow(exclusions) > 0) {
    log_exclusion(logger, exclusion_log_path, exclusions$row_id, exclusions$reason, "ingest")
    log_info(logger, "Exclusions logged to %s", exclusion_log_path)
  }

  # Save cleaned data
  log_info(logger, "Saving cleaned data to %s", output_path)
  tryCatch({
    write.csv(cleaned_data, output_path, row.names = FALSE)
    log_info(logger, "Successfully saved %d rows to %s", nrow(cleaned_data), output_path)
  }, error = function(e) {
    log_error(logger, "Failed to save cleaned data: %s", e$message)
    log_abort(logger, "Pipeline aborted: Could not write output file.")
    quit(status = 1)
  })

  # Save exclusion summary to JSON for report
  exclusion_summary <- list(
    total_rows = total_rows,
    excluded_rows = current_excluded,
    exclusion_rate = exclusion_rate,
    steps = list(
      list(step = "ingest", excluded = current_excluded, reason = "missing_acute_sleepiness")
    )
  )
  jsonlite::write_json(exclusion_summary, file.path(get_project_root(), "data", "derived", "exclusion_counts.json"), auto_unbox = TRUE)

  log_info(logger, "Ingestion complete. Exclusion rate: %.2f%%", exclusion_rate * 100)
  quit(status = 0)
}

# Run main
main()
