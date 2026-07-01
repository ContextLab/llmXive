# tests/unit/test_utils.R
# Unit tests for utils.R (T004)
# Tests logging, directory creation, checksums, and data validation

library(testthat)
library(here)

# Source the utils file
# Assuming project structure: src/code/utils.R
# We need to ensure the path is correct relative to the test execution
utils_path <- here::here("src", "code", "utils.R")

# Skip if utils.R doesn't exist yet (should exist after T004)
if (!file.exists(utils_path)) {
  test_that("utils.R exists", {
    expect_true(file.exists(utils_path), info = "utils.R must exist for testing")
  })
} else {
  source(utils_path)

  # --- Test Directory Helpers ---
  test_that("ensure_directory creates missing directories", {
    temp_dir <- tempfile()
    sub_dir <- file.path(temp_dir, "nested", "dir")
    expect_false(dir.exists(sub_dir))

    result <- ensure_directory(sub_dir)

    expect_true(dir.exists(sub_dir))
    expect_equal(result, sub_dir)

    # Cleanup
    unlink(temp_dir, recursive = TRUE)
  })

  test_that("ensure_directory handles existing directories", {
    temp_dir <- tempfile()
    expect_true(dir.exists(temp_dir))

    result <- ensure_directory(temp_dir)

    expect_equal(result, temp_dir)
    unlink(temp_dir, recursive = TRUE)
  })

  # --- Test Checksum Helpers ---
  test_that("get_file_checksum works on existing file", {
    temp_file <- tempfile()
    writeLines("test content", temp_file)

    checksum <- get_file_checksum(temp_file)

    expect_false(is.null(checksum))
    expect_true(nchar(checksum) == 32) # MD5 length

    unlink(temp_file)
  })

  test_that("get_file_checksum returns NULL for missing file", {
    checksum <- get_file_checksum("non_existent_file_xyz.txt")
    expect_null(checksum)
  })

  test_that("validate_checksum returns TRUE for matching checksum", {
    temp_file <- tempfile()
    writeLines("test content", temp_file)
    correct_checksum <- get_file_checksum(temp_file)

    result <- validate_checksum(temp_file, correct_checksum)

    expect_true(result)
    unlink(temp_file)
  })

  test_that("validate_checksum returns FALSE for mismatched checksum", {
    temp_file <- tempfile()
    writeLines("test content", temp_file)

    result <- validate_checksum(temp_file, "wrong_checksum_123456789012")

    expect_false(result)
    unlink(temp_file)
  })

  # --- Test Data Validation Helpers ---
  test_that("check_missing_climate_values detects NAs", {
    df <- data.frame(
      temp = c(10.5, NA, 12.0),
      precip = c(50.0, 60.0, NA),
      other = c(1, 2, 3)
    )

    result <- check_missing_climate_values(df, c("temp", "precip"))

    expect_true(is.list(result))
    expect_length(result, 2)

    # Check temp
    temp_res <- result[[1]]
    expect_equal(temp_res$column, "temp")
    expect_equal(temp_res$na_count, 1)

    # Check precip
    precip_res <- result[[2]]
    expect_equal(precip_res$column, "precip")
    expect_equal(precip_res$na_count, 1)
  })

  test_that("check_missing_climate_values handles missing columns", {
    df <- data.frame(temp = c(10.5, 12.0))
    result <- check_missing_climate_values(df, c("temp", "precip"))
    expect_null(result)
  })

  test_that("check_coordinate_precision flags high uncertainty", {
    df <- data.frame(
      longitude = c(10, 20, 30),
      latitude = c(40, 50, 60),
      coordinateUncertaintyInMeters = c(5000, 15000, 1000)
    )

    result <- check_coordinate_precision(df, "coordinateUncertaintyInMeters", threshold_km = 10)

    expect_equal(result$status, "checked")
    expect_equal(result$records_flagged, 1) # Only 15000 > 10000
    expect_equal(result$records_na_uncertainty, 0)
  })

  test_that("check_coordinate_precision handles NA uncertainty", {
    df <- data.frame(
      longitude = c(10, 20),
      latitude = c(40, 50),
      coordinateUncertaintyInMeters = c(5000, NA)
    )

    result <- check_coordinate_precision(df, "coordinateUncertaintyInMeters", threshold_km = 10)

    expect_equal(result$status, "checked")
    expect_equal(result$records_flagged, 0)
    expect_equal(result$records_na_uncertainty, 1)
  })

  test_that("check_coordinate_precision handles missing column", {
    df <- data.frame(longitude = c(10), latitude = c(40))
    result <- check_coordinate_precision(df, "coordinateUncertaintyInMeters", threshold_km = 10)

    expect_equal(result$status, "column_missing")
  })

  # --- Test Logging Helpers (Basic) ---
  test_that("log functions execute without error", {
    # Initialize logger to a temp file
    temp_log <- tempfile(fileext = ".log")
    init_logger(temp_log)

    expect_silent(log_info("Test info message"))
    expect_silent(log_warn("Test warning message"))
    expect_silent(log_error("Test error message"))

    # Verify file exists and has content
    expect_true(file.exists(temp_log))
    expect_true(file.info(temp_log)$size > 0)

    # Cleanup
    unlink(temp_log)
  })
}
