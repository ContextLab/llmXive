#!/usr/bin/env Rscript
# Task T011: Implement data ingestion and initial cleaning for US1
# Dependencies: code/00_config.R, code/utils_validation.R, code/utils_logging.R

# Load configuration
source("code/00_config.R")

# Load utility functions
source("code/utils_validation.R")
source("code/utils_logging.R")

# Define required columns based on FR-001 and task description
REQUIRED_COLUMNS <- c("MEQ_score", "MFQ_1", "MFQ_2", "MFQ_3", "MFQ_4", "MFQ_5", 
                      "MFQ_6", "MFQ_7", "MFQ_8", "MFQ_9", "MFQ_10", "MFQ_11", 
                      "MFQ_12", "MFQ_13", "MFQ_14", "MFQ_15", "MFQ_16", "MFQ_17", 
                      "MFQ_18", "MFQ_19", "MFQ_20", "PSQI", "acute_sleepiness", 
                      "age", "sex")

# Note: The exact MFQ column names (MFQ_1..MFQ_20) are assumed based on standard 
# Morningness-Eveningness Questionnaire structure. In a real implementation, 
# these would be defined in code/measurements.md (T005) and validated against T005.

main <- function() {
  log_info("Starting data ingestion process (T011)...")
  
  # Ensure output directories exist
  if (!dir.exists(OUTPUT_PROCESSED)) {
    dir.create(OUTPUT_PROCESSED, recursive = TRUE)
  }
  if (!dir.exists(OUTPUT_DERIVED)) {
    dir.create(OUTPUT_DERIVED, recursive = TRUE)
  }
  if (!dir.exists(LOGS_DIR)) {
    dir.create(LOGS_DIR, recursive = TRUE)
  }
  
  # Check if raw data exists
  if (!file.exists(RAW_DATA_PATH)) {
    log_error(paste("Raw data file not found:", RAW_DATA_PATH))
    stop("Raw data file not found. Please ensure data is available at the specified path.")
  }
  
  # Load raw data
  log_info(paste("Loading raw data from:", RAW_DATA_PATH))
  tryCatch({
    raw_data <- read.csv(RAW_DATA_PATH, stringsAsFactors = FALSE)
  }, error = function(e) {
    log_error(paste("Failed to load raw data:", e$message))
    stop(e)
  })
  
  original_rows <- nrow(raw_data)
  log_info(paste("Loaded", original_rows, "rows"))
  
  # Validate required columns
  log_info("Validating required columns...")
  missing_cols <- validate_required_columns(raw_data, REQUIRED_COLUMNS)
  
  if (length(missing_cols) > 0) {
    log_error(paste("Missing required columns:", paste(missing_cols, collapse = ", ")))
    log_error("ABORTING: FR-001 violation - missing required columns")
    stop("ABORT: Missing required columns. Pipeline cannot proceed.")
  }
  
  log_info("All required columns present")
  
  # Track exclusions
  exclusion_log_file <- file.path(LOGS_DIR, "ingest_exclusions.log")
  excluded_rows <- data.frame(
    row_id = integer(),
    reason = character(),
    stringsAsFactors = FALSE
  )
  
  # Process missing acute_sleepiness values
  log_info("Checking for missing acute_sleepiness values...")
  missing_sleepiness <- which(is.na(raw_data$acute_sleepiness))
  
  if (length(missing_sleepiness) > 0) {
    log_info(paste("Found", length(missing_sleepiness), "rows with missing acute_sleepiness"))
    
    # Log exclusions
    for (idx in missing_sleepiness) {
      excluded_rows <- rbind(excluded_rows, data.frame(
        row_id = idx,
        reason = "missing_acute_sleepiness",
        stringsAsFactors = FALSE
      ))
    }
    
    # Write to log file
    log_exclusions(excluded_rows, exclusion_log_file)
    
    # Remove excluded rows
    raw_data <- raw_data[-missing_sleepiness, ]
  }
  
  # Save cleaned data
  cleaned_data_path <- file.path(OUTPUT_PROCESSED, "cleaned_data.csv")
  log_info(paste("Saving cleaned data to:", cleaned_data_path))
  write.csv(raw_data, cleaned_data_path, row.names = FALSE)
  
  # Save exclusion count
  exclusion_count_path <- file.path(OUTPUT_DERIVED, "ingest_exclusion_count.json")
  exclusion_summary <- list(
    total_original_rows = original_rows,
    rows_excluded_missing_sleepiness = length(missing_sleepiness),
    rows_remaining = nrow(raw_data),
    exclusion_timestamp = Sys.time()
  )
  
  log_info(paste("Saving exclusion count to:", exclusion_count_path))
  writeLines(toJSON(exclusion_summary, pretty = TRUE), exclusion_count_path)
  
  log_info(paste("Ingestion complete. Original rows:", original_rows, 
                "Excluded:", length(missing_sleepiness), 
                "Remaining:", nrow(raw_data)))
  
  invisible(raw_data)
}

# Helper function to log exclusions
log_exclusions <- function(excluded_data, log_file) {
  if (!file.exists(log_file)) {
    # Create header if file doesn't exist
    header <- "row_id,reason\n"
    writeLines(header, log_file)
  }
  
  # Append exclusions
  exclusion_text <- apply(excluded_data, 1, function(row) {
    paste(row["row_id"], row["reason"], sep = ",")
  })
  
  writeLines(exclusion_text, log_file, append = TRUE)
}

# Run main function
main()
