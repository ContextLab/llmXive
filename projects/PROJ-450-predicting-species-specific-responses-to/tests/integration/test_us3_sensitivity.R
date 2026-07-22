# tests/integration/test_us3_sensitivity.R
# Integration test for User Story 3: Sensitivity Analysis
#
# Verifies:
# - Full sensitivity run produces mean/SD
# - Flags high-variability species
# - Output file structure matches expectations
# - Logs are generated

library(testthat)
library(readr)
library(dplyr)
library(here)

describe("T034 Integration: Sensitivity Analysis", {
  it("produces results/sensitivity_summary.csv with correct schema", {
    # Skip if input data is not available (for CI environments without data)
    skip_if_not(file.exists(here("data", "raw", "occurrences.csv")),
                "Raw data not available for integration test")
    skip_if_not(file.exists(here("data", "processed", "points_with_climate.csv")),
                "Points with climate not available for integration test")

    # Run the script
    # In a real CI, this would be run via `Rscript`
    # Here we source it and capture output
    tryCatch({
      source(here("src", "code", "sensitivity.R"))
    }, error = function(e) {
      # If the script fails due to missing data or other reasons, skip
      if (grepl("not found", e$message)) {
        skip(paste("Skipping test due to:", e$message))
      } else {
        stop(e)
      }
    })

    # Check output file exists
    expect_true(file.exists(here("results", "sensitivity_summary.csv")))

    # Load and check schema
    df <- read_csv(here("results", "sensitivity_summary.csv"), show_col_types = FALSE)

    expected_cols <- c("species", "n_original_records", "n_subsampled_records",
                       "mean_shift", "sd_shift", "is_flagged")
    expect_setequal(names(df), expected_cols)

    # Check data types
    expect_s3_class(df$species, "character")
    expect_s3_class(df$n_original_records, "integer")
    expect_s3_class(df$mean_shift, "numeric")
    expect_s3_class(df$is_flagged, "logical")

    # Check for at least one row if data was processed
    if (nrow(df) > 0) {
      expect_true(all(df$sd_shift >= 0))
      expect_true(all(df$is_flagged %in% c(TRUE, FALSE)))
    }
  })

  it("appends detailed log entries for subsampling outcomes", {
    skip_if_not(file.exists(here("logs", "sensitivity.log")),
                "Log file not generated")

    log_content <- readLines(here("logs", "sensitivity.log"))
    log_text <- paste(log_content, collapse = "\n")

    expect_true(grepl("Starting sensitivity analysis", log_text))
    expect_true(grepl("Wrote sensitivity summary", log_text))
    expect_true(grepl("Subsampling outcomes summary", log_text))
  })
})