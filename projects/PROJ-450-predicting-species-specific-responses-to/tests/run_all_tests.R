#!/usr/bin/env Rscript
# T035: Run testthat suite for all unit and integration tests
# This script discovers and runs all tests in the tests/ directory
# and exits with a non-zero status if any tests fail.

# Load required libraries
suppressPackageStartupMessages({
  library(testthat)
  library(dplyr)
  library(stringr)
})

# Set project root using here if available, otherwise fallback to relative
if (requireNamespace("here", quietly = TRUE)) {
  setwd(here::here())
}

# Define test directories relative to project root
unit_test_dir <- "tests/unit"
integration_test_dir <- "tests/integration"

# Collect all test files
test_files <- c()

if (dir.exists(unit_test_dir)) {
  unit_files <- list.files(unit_test_dir, pattern = "^test.*\\.R$", full.names = TRUE, recursive = TRUE)
  test_files <- c(test_files, unit_files)
}

if (dir.exists(integration_test_dir)) {
  integration_files <- list.files(integration_test_dir, pattern = "^test.*\\.R$", full.names = TRUE, recursive = TRUE)
  test_files <- c(test_files, integration_files)
}

if (length(test_files) == 0) {
  cat("WARNING: No test files found in", unit_test_dir, "or", integration_test_dir, "\n")
  cat("Task T035 requires test files to exist. Please ensure tests are implemented.\n")
  quit(status = 1)
}

cat("Found", length(test_files), "test files:\n")
print(test_files)
cat("\n")

# Run tests with reporter
# Use 'summary' reporter for concise output, 'fail' to stop on first error
reporter <- MultiReporter$new(reporters = list(
  ListReporter$new(),
  SummaryReporter$new()
))

# Source test files and run tests
test_results <- test_dir(
  path = unit_test_dir,
  reporter = reporter,
  stop_on_failure = FALSE,
  stop_on_warning = FALSE,
  load_helpers = TRUE
)

test_results2 <- test_dir(
  path = integration_test_dir,
  reporter = reporter,
  stop_on_failure = FALSE,
  stop_on_warning = FALSE,
  load_helpers = TRUE
)

# Aggregate results
all_results <- c(test_results, test_results2)

# Check for failures
failed_tests <- sum(sapply(all_results, function(x) length(x$failures)) > 0)
total_tests <- length(all_results)

cat("\n--- Test Summary ---\n")
cat("Total test suites:", total_tests, "\n")
cat("Suites with failures:", failed_tests, "\n")

if (failed_tests > 0) {
  cat("\n❌ T035 FAILED: One or more test suites had failures.\n")
  quit(status = 1)
} else {
  cat("\n✅ T035 PASSED: All test suites executed successfully.\n")
  quit(status = 0)
}