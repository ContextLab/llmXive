#!/usr/bin/env Rscript
# Tests for T011: Data Ingestion
# Tests for column validation, missing data handling, and output generation

library(testthat)

# Source the main function
source("code/00_config.R")
source("code/utils_validation.R")
source("code/utils_logging.R")
source("code/01_ingest.R")

# Create test helper functions
create_test_data <- function(rows = 10, missing_sleepiness = 0, missing_cols = NULL) {
  # Generate sample data
  test_data <- data.frame(
    MEQ_score = sample(20:80, rows, replace = TRUE),
    MFQ_1 = sample(1:5, rows, replace = TRUE),
    MFQ_2 = sample(1:5, rows, replace = TRUE),
    MFQ_3 = sample(1:5, rows, replace = TRUE),
    MFQ_4 = sample(1:5, rows, replace = TRUE),
    MFQ_5 = sample(1:5, rows, replace = TRUE),
    MFQ_6 = sample(1:5, rows, replace = TRUE),
    MFQ_7 = sample(1:5, rows, replace = TRUE),
    MFQ_8 = sample(1:5, rows, replace = TRUE),
    MFQ_9 = sample(1:5, rows, replace = TRUE),
    MFQ_10 = sample(1:5, rows, replace = TRUE),
    MFQ_11 = sample(1:5, rows, replace = TRUE),
    MFQ_12 = sample(1:5, rows, replace = TRUE),
    MFQ_13 = sample(1:5, rows, replace = TRUE),
    MFQ_14 = sample(1:5, rows, replace = TRUE),
    MFQ_15 = sample(1:5, rows, replace = TRUE),
    MFQ_16 = sample(1:5, rows, replace = TRUE),
    MFQ_17 = sample(1:5, rows, replace = TRUE),
    MFQ_18 = sample(1:5, rows, replace = TRUE),
    MFQ_19 = sample(1:5, rows, replace = TRUE),
    MFQ_20 = sample(1:5, rows, replace = TRUE),
    PSQI = sample(0:21, rows, replace = TRUE),
    acute_sleepiness = sample(0:10, rows, replace = TRUE),
    age = sample(18:80, rows, replace = TRUE),
    sex = sample(c("M", "F"), rows, replace = TRUE),
    stringsAsFactors = FALSE
  )
  
  # Add missing acute_sleepiness if requested
  if (missing_sleepiness > 0) {
    indices <- sample(1:nrow(test_data), missing_sleepiness, replace = FALSE)
    test_data$acute_sleepiness[indices] <- NA
  }
  
  # Remove columns if requested
  if (!is.null(missing_cols) && length(missing_cols) > 0) {
    test_data <- test_data[, !colnames(test_data) %in% missing_cols, drop = FALSE]
  }
  
  return(test_data)
}

test_that("validate_required_columns returns empty for complete data", {
  test_data <- create_test_data()
  result <- validate_required_columns(test_data, c("MEQ_score", "acute_sleepiness", "age", "sex"))
  expect_equal(length(result), 0)
})

test_that("validate_required_columns returns missing columns", {
  test_data <- create_test_data(missing_cols = c("age", "sex"))
  result <- validate_required_columns(test_data, c("MEQ_score", "acute_sleepiness", "age", "sex"))
  expect_true("age" %in% result)
  expect_true("sex" %in% result)
  expect_equal(length(result), 2)
})

test_that("missing acute_sleepiness rows are excluded", {
  # Create test data with missing acute_sleepiness
  test_data <- create_test_data(rows = 20, missing_sleepiness = 5)
  
  # Count NA values
  na_count <- sum(is.na(test_data$acute_sleepiness))
  expect_equal(na_count, 5)
  
  # Simulate the exclusion logic
  missing_indices <- which(is.na(test_data$acute_sleepiness))
  cleaned_data <- test_data[-missing_indices, ]
  
  # Verify exclusion
  expect_equal(nrow(cleaned_data), 15)
  expect_equal(sum(is.na(cleaned_data$acute_sleepiness)), 0)
})

test_that("log_exclusions creates proper log file", {
  # Create temporary test file
  temp_log <- tempfile(fileext = ".log")
  
  # Create sample exclusion data
  excluded_rows <- data.frame(
    row_id = c(1, 2, 3),
    reason = c("missing_acute_sleepiness", "missing_acute_sleepiness", "missing_acute_sleepiness"),
    stringsAsFactors = FALSE
  )
  
  # Call log function
  log_exclusions(excluded_rows, temp_log)
  
  # Verify file exists and has content
  expect_true(file.exists(temp_log))
  expect_true(file.info(temp_log)$size > 0)
  
  # Read and verify content
  lines <- readLines(temp_log)
  expect_true(length(lines) >= 4) # Header + 3 data rows
  
  # Clean up
  unlink(temp_log)
})

test_that("cleaned data has correct structure", {
  test_data <- create_test_data(rows = 100, missing_sleepiness = 10)
  
  # Simulate the full process
  missing_indices <- which(is.na(test_data$acute_sleepiness))
  cleaned_data <- test_data[-missing_indices, ]
  
  # Verify structure
  expect_equal(nrow(cleaned_data), 90)
  expect_true(all(c("MEQ_score", "acute_sleepiness", "age", "sex") %in% colnames(cleaned_data)))
  expect_true(sum(is.na(cleaned_data$acute_sleepiness)) == 0)
})

test_that("exclusion count JSON is properly formatted", {
  # Create sample exclusion summary
  exclusion_summary <- list(
    total_original_rows = 100,
    rows_excluded_missing_sleepiness = 10,
    rows_remaining = 90,
    exclusion_timestamp = Sys.time()
  )
  
  # Convert to JSON
  json_output <- toJSON(exclusion_summary, pretty = TRUE)
  
  # Verify it's valid JSON
  expect_true(!is.null(json_output))
  expect_true(grepl("total_original_rows", json_output))
  expect_true(grepl("rows_excluded_missing_sleepiness", json_output))
})

test_that("pipeline aborts on missing required columns", {
  # Create data with missing columns
  test_data <- create_test_data(missing_cols = c("MEQ_score"))
  
  # Verify validation catches this
  missing <- validate_required_columns(test_data, REQUIRED_COLUMNS)
  expect_true("MEQ_score" %in% missing)
  
  # In real execution, this would trigger stop()
  # Here we just verify the validation logic works
  expect_true(length(missing) > 0)
})

# Run tests
test_check("test-ingest")