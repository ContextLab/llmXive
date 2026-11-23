# tests/integration/test_us1_centroids.R
# Integration test for User Story 1 (T013-T015a)
# Verifies full centroid generation for multiple species produces correct CSV schema

library(testthat)

test_that("US1 Integration: Full centroid generation produces correct schema", {
  # This test assumes the pipeline has run up to T015a
  # We check the existence and schema of data/processed/centroids.csv
  
  centroids_file <- "data/processed/centroids.csv"
  
  # Skip if file doesn't exist (pipeline not run yet)
  if (!file.exists(centroids_file)) {
    skip("data/processed/centroids.csv not found. Run pipeline first.")
  }
  
  # Read the file
  df <- read.csv(centroids_file, stringsAsFactors = FALSE)
  
  # Check required columns
  required_cols <- c("species", "period", "temp", "precip", "record_count", "computed_at")
  expect_true(all(required_cols %in% names(df)))
  
  # Check data types
  expect_true(is.numeric(df$temp))
  expect_true(is.numeric(df$precip))
  expect_true(is.numeric(df$record_count))
  expect_true(is.character(df$species))
  expect_true(is.character(df$period))
  
  # Check period values
  expect_true(all(df$period %in% c("1970-2000", "1991-2020")))
  
  # Check that we have at least one record per period for at least one species
  # (Assuming the input data was valid)
  if (nrow(df) > 0) {
    expect_true(nrow(unique(df$species)) >= 1)
    expect_true(nrow(unique(df$period)) >= 1)
  }
  
  # Check that record_count is positive
  expect_true(all(df$record_count > 0))
  
  # Check that computed_at is a valid timestamp string
  expect_true(all(grepl("\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}", df$computed_at)))
})

test_that("US1 Integration: Centroids match raw data means", {
  # If points_with_climate.csv exists, verify the means
  points_file <- "data/processed/points_with_climate.csv"
  centroids_file <- "data/processed/centroids.csv"
  
  if (!file.exists(points_file) || !file.exists(centroids_file)) {
    skip("Input or output files missing for verification.")
  }
  
  points_df <- read.csv(points_file, stringsAsFactors = FALSE)
  centroids_df <- read.csv(centroids_file, stringsAsFactors = FALSE)
  
  # Filter valid rows
  required_cols <- c("species", "period", "temp", "precip")
  points_df$temp <- as.numeric(points_df$temp)
  points_df$precip <- as.numeric(points_df$precip)
  valid_rows <- complete.cases(points_df[, required_cols])
  points_df <- points_df[valid_rows, ]
  
  # Compute expected means
  expected_means <- aggregate(
    cbind(temp, precip) ~ species + period,
    data = points_df,
    FUN = mean,
    na.rm = TRUE
  )
  
  # Merge with actual centroids
  merged <- merge(centroids_df, expected_means, 
                  by = c("species", "period"), 
                  suffixes = c("_actual", "_expected"))
  
  # Check that means are approximately equal (allowing for floating point)
  expect_true(all(abs(merged$temp_actual - merged$temp_expected) < 1e-6))
  expect_true(all(abs(merged$precip_actual - merged$precip_expected) < 1e-6))
})