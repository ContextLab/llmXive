# tests/unit/test_utils.R
# Task: T009
# Description: Unit tests for logging, directory creation, checksum functions, and coordinate validation logic.

library(testthat)

# Source the utils file
# Note: In a real run, we need to set the working directory or use here::here()
# For unit tests, we assume utils.R is in src/code/
# We will source it relative to the test file location (tests/unit/)
# Assuming standard structure: tests/unit/../src/code/utils.R
utils_path <- file.path("src", "code", "utils.R")
if (file.exists(utils_path)) {
  source(utils_path)
} else {
  # Fallback for CI if path differs
  source("../../src/code/utils.R")
}

test_that("create_dir_if_missing creates directory", {
  test_dir <- file.path("tests", "tmp_test_dir")
  if (dir.exists(test_dir)) unlink(test_dir, recursive = TRUE)
  
  create_dir_if_missing(test_dir)
  expect_true(dir.exists(test_dir))
  
  # Cleanup
  unlink(test_dir, recursive = TRUE)
})

test_that("create_dir_if_missing does nothing if exists", {
  test_dir <- file.path("tests", "tmp_test_dir")
  dir.create(test_dir, recursive = TRUE, showWarnings = FALSE)
  
  create_dir_if_missing(test_dir)
  expect_true(dir.exists(test_dir))
  
  # Cleanup
  unlink(test_dir, recursive = TRUE)
})

test_that("compute_checksum returns NA for missing file", {
  checksum <- compute_checksum("non_existent_file.txt")
  expect_true(is.na(checksum))
})

test_that("compute_checksum returns string for existing file", {
  # Create a temp file
  tmp_file <- tempfile()
  writeLines("test", tmp_file)
  
  checksum <- compute_checksum(tmp_file)
  expect_true(is.character(checksum))
  expect_true(nchar(checksum) > 0)
  
  unlink(tmp_file)
})

test_that("validate_checksum works", {
  tmp_file <- tempfile()
  writeLines("test", tmp_file)
  checksum <- compute_checksum(tmp_file)
  
  expect_true(validate_checksum(tmp_file, checksum))
  expect_false(validate_checksum(tmp_file, "wrong_checksum"))
  
  unlink(tmp_file)
})

test_that("is_valid_climate handles NA", {
  expect_false(is_valid_climate(NA))
  expect_true(is_valid_climate(10.5))
  expect_true(is_valid_climate(0))
})

test_that("check_coordinate_precision handles missing column", {
  df <- data.frame(x = 1:5)
  result <- check_coordinate_precision(df, "uncertainty")
  expect_true(all(result))
})

test_that("check_coordinate_precision filters high uncertainty", {
  df <- data.frame(
    x = 1:5,
    coordinateUncertaintyInMeters = c(5000, 15000, NA, 9999, 20000)
  )
  result <- check_coordinate_precision(df, "coordinateUncertaintyInMeters", 10000)
  # Expected: TRUE, FALSE, TRUE, TRUE, FALSE
  expected <- c(TRUE, FALSE, TRUE, TRUE, FALSE)
  expect_identical(result, expected)
})

test_that("validate_coordinates filters NA and 0,0", {
  df <- data.frame(
    decimalLatitude = c(45, NA, 0, 46, 0),
    decimalLongitude = c(-75, -75, 0, NA, 0)
  )
  result <- validate_coordinates(df)
  # Expected: TRUE, FALSE, FALSE, FALSE, FALSE (0,0 is invalid)
  expected <- c(TRUE, FALSE, FALSE, FALSE, FALSE)
  expect_identical(result, expected)
})
