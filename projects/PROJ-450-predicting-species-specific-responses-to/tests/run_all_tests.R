#!/usr/bin/env Rscript
# ============================================================================
# Task: T035 - Run testthat suite for all unit and integration tests
# Description: Executes the full test suite for the project.
#              Reads tests from tests/unit/ and tests/integration/.
#              Outputs results to console and a TAP report file.
# ============================================================================

# Load required packages
if (!requireNamespace("testthat", quietly = TRUE)) {
  stop("Package 'testthat' is required but not installed. Please run: install.packages('testthat')")
}
if (!requireNamespace("here", quietly = TRUE)) {
  stop("Package 'here' is required but not installed. Please run: install.packages('here')")
}

library(testthat)
library(here)

# Set project root explicitly if 'here' fails to detect automatically
# This ensures robustness when running from CI or different working directories
project_root <- here::here()
setwd(project_root)

cat("\n")
cat("============================================================================\n")
cat("Running Full Test Suite for Project: Predicting Species-Specific Responses\n")
cat("============================================================================\n")
cat("Working Directory:", getwd(), "\n")
cat("Started at:", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "\n")
cat("-----------------------------------------------------------------------------\n\n")

# Define test paths relative to project root
# We expect the structure: tests/unit/ and tests/integration/
unit_test_dir <- file.path("tests", "unit")
integration_test_dir <- file.path("tests", "integration")

# Verify directories exist
if (!dir.exists(unit_test_dir)) {
  warning("Unit test directory 'tests/unit' not found. Skipping unit tests.")
}
if (!dir.exists(integration_test_dir)) {
  warning("Integration test directory 'tests/integration' not found. Skipping integration tests.")
}

# Prepare a summary report file
report_file <- file.path("results", "test_results_tap.txt")
dir.create(dirname(report_file), showWarnings = FALSE, recursive = TRUE)

# Open connection for TAP report
con <- file(report_file, open = "w")
on.exit(close(con), add = TRUE)

# Write TAP header
cat("TAP version 13\n", file = con)

# Helper to run a directory of tests and append to report
run_test_dir <- function(dir_path, label) {
  if (!dir.exists(dir_path)) return()

  cat("\n>>> Running", label, "...\n")
  cat(">>> Path:", dir_path, "\n")

  # Get all R files in the directory
  test_files <- list.files(dir_path, pattern = "\\.R$", full.names = TRUE)

  if (length(test_files) == 0) {
    cat("No test files found in", dir_path, "\n")
    return()
  }

  # Run tests using testthat
  # We capture the output to print to console and write to TAP file
  results <- list()
  total_tests <- 0
  passed_tests <- 0
  failed_tests <- 0

  for (tf in test_files) {
    cat("  - Running:", basename(tf), "\n")
    
    # Run the specific file
    # test_dir or test_file returns a list of results
    tryCatch({
      res <- test_file(tf, reporter = "summary", stop_on_failure = FALSE)
      
      # Aggregate results manually if possible, or just rely on exit code
      # For TAP output, we iterate through the results if available
      if (inherits(res, "testthat_results")) {
         # Extract counts
         # Note: testthat 3e returns a list with 'results' and 'errors'
         # We'll rely on the console output for detailed failure messages
         # and just track the overall success for the summary
      }
    }, error = function(e) {
      cat("  ERROR running", basename(tf), ":", conditionMessage(e), "\n")
      cat("Error #", length(results) + 1, ": ", conditionMessage(e), "\n", file = con)
    })
  }

  # Since we are using summary reporter, we rely on the exit code of the process
  # But for the TAP file, we need to know if the suite passed.
  # We will assume pass unless the script exits with error.
  cat("  [", label, "] Completed.\n")
}

# Run Unit Tests
run_test_dir(unit_test_dir, "UNIT TESTS")

# Run Integration Tests
run_test_dir(integration_test_dir, "INTEGRATION TESTS")

# Final Summary
cat("\n============================================================================\n")
cat("Test Suite Execution Complete\n")
cat("============================================================================\n")
cat("Report saved to:", report_file, "\n")
cat("Finished at:", format(Sys.time(), "%Y-%m-%d %H:%M:%S"), "\n")

# Exit with status code based on test success
# testthat::test_dir exits with 1 on failure if stop_on_failure is TRUE (default)
# Since we ran test_file individually above, we need to ensure the script fails if tests failed.
# We will re-run with a reporter that returns a status we can check, or simply let the 
# last test_file determine the exit if we didn't catch errors. 
# To be safe and explicit:

# Re-run with stop_on_failure to ensure CI/CD pipelines catch errors
# We wrap in tryCatch to print a final status message
final_status <- 0

# Run Unit Tests again for strict checking
if (dir.exists(unit_test_dir)) {
  tryCatch({
    test_dir(unit_test_dir, reporter = "summary", stop_on_failure = TRUE)
  }, exit = function(e) {
    final_status <<- 1
    cat("\n!!! UNIT TESTS FAILED !!!\n")
  })
}

if (final_status == 0 && dir.exists(integration_test_dir)) {
  tryCatch({
    test_dir(integration_test_dir, reporter = "summary", stop_on_failure = TRUE)
  }, exit = function(e) {
    final_status <<- 1
    cat("\n!!! INTEGRATION TESTS FAILED !!!\n")
  })
}

if (final_status == 0) {
  cat("\n*** ALL TESTS PASSED ***\n")
} else {
  cat("\n*** TEST SUITE FAILED ***\n")
  quit(status = 1)
}