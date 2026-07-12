#!/usr/bin/env Rscript
# T027: Validation Script for Sensitivity Analysis
# Ensures the sensitivity sweep meets project requirements.

library(readr)
library(dplyr)

SENSITIVITY_FILE <- "data/derived/sensitivity_sweep.csv"
REPORT_FILE <- "reports/chronotype_moral_analysis.html"

run_validation <- function() {
  cat("Starting sensitivity analysis validation...\n")

  # Check file existence
  if (!file.exists(SENSITIVITY_FILE)) {
    stop("FAIL: Sensitivity sweep file not found at ", SENSITIVITY_FILE)
  }

  # Load data
  df <- read_csv(SENSITIVITY_FILE, show_col_types = FALSE)

  # Check columns
  required_cols <- c("subscale", "alpha_threshold", "p_value", "significant")
  missing <- setdiff(required_cols, names(df))
  if (length(missing) > 0) {
    stop("FAIL: Missing columns: ", paste(missing, collapse = ", "))
  }

  # Check thresholds
  expected_thresholds <- c(0.01, 0.0125, 0.015)
  found_thresholds <- unique(df$alpha_threshold)
  if (!all(expected_thresholds %in% found_thresholds)) {
    stop("FAIL: Missing expected alpha thresholds. Found: ", 
         paste(found_thresholds, collapse = ", "))
  }

  # Check row count (should be at least 3 thresholds * 5 subscales = 15)
  min_rows <- length(expected_thresholds) * 5 # Assuming 5 subscales
  if (nrow(df) < min_rows) {
    warning("WARN: Row count (", nrow(df), ") is less than expected minimum (", min_rows, ")")
  }

  # Check for valid p-values
  if (any(df$p_value < 0 | df$p_value > 1, na.rm = TRUE)) {
    stop("FAIL: Invalid p-values detected (must be between 0 and 1)")
  }

  # Check for logical significant column
  if (!is.logical(df$significant)) {
    stop("FAIL: 'significant' column must be logical/boolean")
  }

  cat("PASS: Sensitivity analysis validation successful.\n")
  cat("  - File exists\n")
  cat("  - Columns correct\n")
  cat("  - Thresholds present\n")
  cat("  - Data types valid\n")
  return(TRUE)
}

# Run validation
tryCatch({
  run_validation()
  quit(status = 0)
}, error = function(e) {
  cat("FAIL: Validation failed -", e$message, "\n")
  quit(status = 1)
})
