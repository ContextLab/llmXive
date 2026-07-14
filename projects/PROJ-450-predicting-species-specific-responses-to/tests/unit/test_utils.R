# tests/unit/test_utils.R
# Unit tests for src/code/utils.R functions
# Verifies: logging, directory creation, checksum validation, coordinate precision checks

library(testthat)
library(tools)

# Load the utils module
# We source it directly to ensure we have the latest implementation
utils_path <- file.path("src", "code", "utils.R")
if (!file.exists(utils_path)) {
  stop("utils.R not found at src/code/utils.R. Please ensure T004 is completed.")
}
source(utils_path)

# --------------------------------------------------------------------------
# Test Setup: Temporary Directory for File System Tests
# --------------------------------------------------------------------------
test_dir <- tempfile(pattern = "utils_test_")
test_subdir <- file.path(test_dir, "subdir")
test_nested <- file.path(test_dir, "level1", "level2")

# Clean up after all tests
on.exit({
  if (dir.exists(test_dir)) {
    unlink(test_dir, recursive = TRUE)
  }
})

# --------------------------------------------------------------------------
# Test Group: Logging Infrastructure
# --------------------------------------------------------------------------
test_that("logging functions create valid log entries", {
  log_file <- file.path(test_dir, "test_log.log")

  # Test write_log
  expect_silent(write_log(log_file, "Test message", level = "INFO"))
  expect_true(file.exists(log_file))

  content <- readLines(log_file, warn = FALSE)
  expect_true(length(content) >= 1)
  expect_true(grepl("Test message", content[length(content)]))
  expect_true(grepl("INFO", content[length(content)]))

  # Test log_error (should capture timestamp and error message)
  log_error(log_file, "Simulated error")
  content <- readLines(log_file, warn = FALSE)
  expect_true(grepl("ERROR", content[length(content)]))
  expect_true(grepl("Simulated error", content[length(content)]))
})

# --------------------------------------------------------------------------
# Test Group: Directory Creation
# --------------------------------------------------------------------------
test_that("ensure_directory creates directories correctly", {
  # Test creating a single directory
  expect_silent(ensure_directory(test_subdir))
  expect_true(dir.exists(test_subdir))

  # Test creating nested directories (recursive)
  expect_silent(ensure_directory(test_nested))
  expect_true(dir.exists(test_nested))

  # Test that it doesn't error if directory already exists
  expect_silent(ensure_directory(test_subdir))
  expect_true(dir.exists(test_subdir))
})

# --------------------------------------------------------------------------
# Test Group: Checksum Validation
# --------------------------------------------------------------------------
test_that("checksum validation works correctly", {
  # Create a temporary file with known content
  test_file <- file.path(test_dir, "checksum_test.txt")
  writeLines("Hello, World!", test_file)

  # Calculate MD5
  md5_val <- tools::md5sum(test_file)

  # Test valid checksum
  expect_true(validate_checksum(test_file, md5_val))

  # Test invalid checksum
  expect_false(validate_checksum(test_file, "invalid_md5_hash_string"))

  # Test non-existent file
  expect_false(validate_checksum(file.path(test_dir, "nonexistent.txt"), md5_val))
})

# --------------------------------------------------------------------------
# Test Group: Coordinate Validation
# --------------------------------------------------------------------------
test_that("coordinate precision checks work correctly", {
  # Helper to create a minimal data frame for testing
  create_test_df <- function(lat, lon, unc) {
    data.frame(
      decimalLatitude = lat,
      decimalLongitude = lon,
      coordinateUncertaintyInMeters = unc,
      stringsAsFactors = FALSE
    )
  }

  # Test 1: Valid coordinates (uncertainty < 10km)
  df_valid <- create_test_df(45.5, -75.2, 5000) # 5km uncertainty
  expect_true(check_coordinate_precision(df_valid))

  # Test 2: Invalid coordinates (uncertainty >= 10km)
  df_invalid_unc <- create_test_df(45.5, -75.2, 15000) # 15km uncertainty
  expect_false(check_coordinate_precision(df_invalid_unc))

  # Test 3: Missing uncertainty (should be treated as invalid or skipped)
  df_missing_unc <- create_test_df(45.5, -75.2, NA)
  # Assuming the function returns FALSE if uncertainty is NA (cannot verify precision)
  expect_false(check_coordinate_precision(df_missing_unc))

  # Test 4: Mixed validity in a data frame
  df_mixed <- rbind(
    create_test_df(45.5, -75.2, 5000),
    create_test_df(46.0, -76.0, 12000),
    create_test_df(47.0, -77.0, 8000)
  )
  # The function should return TRUE only if ALL rows are valid
  expect_false(check_coordinate_precision(df_mixed))

  # Test 5: Empty data frame
  df_empty <- data.frame(decimalLatitude = numeric(), decimalLongitude = numeric(), coordinateUncertaintyInMeters = numeric())
  expect_true(check_coordinate_precision(df_empty)) # Vacuously true or handled gracefully
})

test_that("handle_missing_climate_values works as expected", {
  # Create a data frame with some NA climate values
  df <- data.frame(
    species = c("A", "B", "C", "D"),
    temp = c(10.5, NA, 12.0, NA),
    precip = c(500.0, 450.0, NA, 600.0),
    stringsAsFactors = FALSE
  )

  # Test filtering
  result <- handle_missing_climate_values(df)

  # Expect only rows with both temp and precip present
  expected_rows <- 2 # Rows A and D
  expect_equal(nrow(result), expected_rows)
  expect_true(all(!is.na(result$temp)))
  expect_true(all(!is.na(result$precip)))
})
