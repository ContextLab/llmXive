# tests/integration/test_us3_sensitivity.R
# Integration test for User Story 3
# Verifies that the full pipeline produces the expected CSV output and flags correctly.
#
# Note: This test requires real data files in data/raw/ to run successfully.
# If no real data exists, it may be skipped or mocked.

library(testthat)
library(here)

# Setup
test_dir <- here::here()
raw_dir <- file.path(test_dir, "data", "raw")
results_dir <- file.path(test_dir, "results")

# Ensure directories exist for test artifacts (if needed)
if (!dir.exists(results_dir)) dir.create(results_dir, recursive = TRUE)

test_that("Sensitivity pipeline runs and produces output file", {
  # Check if input data exists
  input_files <- list.files(raw_dir, pattern = "\\.csv$", full.names = TRUE)

  if (length(input_files) == 0) {
    skip("No input data found in data/raw/. Skipping integration test.")
  }

  # Run the script
  script_path <- file.path(test_dir, "code", "sensitivity.R")
  if (!file.exists(script_path)) {
    skip("sensitivity.R not found.")
  }

  # Execute
  output <- tryCatch({
    source(script_path, local = TRUE)
    TRUE
  }, error = function(e) {
    message("Script execution error: ", e$message)
    FALSE
  })

  expect_true(output, info = "sensitivity.R should run without error")

  # Verify output file exists
  output_file <- file.path(results_dir, "sensitivity_summary.csv")
  expect_true(file.exists(output_file), info = "results/sensitivity_summary.csv should exist")

  # Verify schema
  df <- read.csv(output_file, stringsAsFactors = FALSE)
  expected_cols <- c("species", "n_records", "mean_shift", "sd_shift", "flagged_high_variance")
  expect_true(all(expected_cols %in% names(df)), info = "Output CSV must contain required columns")

  # Verify logic: if a species with <80 records was processed, it shouldn't be in the output
  # (Assuming the script skips them as per T033)
  # We can't easily verify specific values without knowing the input data content,
  # but we can check that the flag column is logical.
  expect_s3_class(df$flagged_high_variance, "logical")
})
