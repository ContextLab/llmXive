#!/usr/bin/env Rscript
# run_all_tests.R
# Executes the full testthat suite for the project.
# Generates a timestamped report in results/test_report.txt

library(testthat)
library(dplyr)
library(lubridate)

# Set project root
here::set_here()

# Define paths
test_dir <- "tests"
output_dir <- "results"
timestamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
report_file <- file.path(output_dir, paste0("test_report_", timestamp, ".txt"))

# Ensure output directory exists
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Capture output to file and console
sink(report_file)
cat("========================================\n")
cat("TEST RUN REPORT\n")
cat("Date:", Sys.time(), "\n")
cat("Working Directory:", getwd(), "\n")
cat("========================================\n\n")

# Counters
total_tests <- 0
passed_tests <- 0
failed_tests <- 0

# Helper to run a test file and capture results
run_test_file <- function(file_path) {
  cat("\n--- Running:", basename(file_path), "---\n")
  
  # Source the file to load test functions (if it's a helper or setup)
  # But for actual test files, we use test_file
  tryCatch({
    result <- test_file(file_path, reporter = "summary", stop_on_failure = FALSE)
    
    # Extract summary stats if possible
    if (!is.null(result$counts)) {
      total_tests <<- total_tests + result$counts$n
      passed_tests <<- passed_tests + result$counts$passed
      failed_tests <<- failed_tests + result$counts$failed
    }
    
    cat("Result: ", ifelse(result$counts$failed == 0, "PASS", "FAIL"), "\n")
    return(result)
  }, error = function(e) {
    cat("ERROR running test file:", conditionMessage(e), "\n")
    failed_tests <<- failed_tests + 1
    return(NULL)
  })
}

# Discover all test files
test_files <- list.files(
  path = test_dir,
  pattern = "\\.R$",
  recursive = TRUE,
  full.names = TRUE
)

cat("Found", length(test_files), "test files.\n")

if (length(test_files) == 0) {
  cat("WARNING: No test files found in", test_dir, "\n")
} else {
  # Run each test file
  for (f in test_files) {
    run_test_file(f)
  }
}

# Summary
cat("\n========================================\n")
cat("SUMMARY\n")
cat("Total Tests:", total_tests, "\n")
cat("Passed:", passed_tests, "\n")
cat("Failed:", failed_tests, "\n")
cat("========================================\n")

# If there were failures, print a specific error message
if (failed_tests > 0) {
  cat("\n⚠️  TEST SUITE FAILED. Please check the report above for details.\n")
  quit(status = 1)
} else {
  cat("\n✅ ALL TESTS PASSED.\n")
}

# Close sink
sink()

# Also print to console for immediate feedback
cat("\nTest report written to:", report_file, "\n")
cat("Final Status: ", ifelse(failed_tests == 0, "SUCCESS", "FAILURE"), "\n")

# Exit with appropriate status code
quit(status = ifelse(failed_tests == 0, 0, 1))
