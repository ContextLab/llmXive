# tests/integration/test_analyze_shifts.R
# Integration test for analyze_shifts.R
# Tests the full pipeline of regression analysis

library(testthat)
library(readr)
library(dplyr)
library(here)

# Source the function to test
source(here("src", "code", "analyze_shifts.R"))

test_that("analyze_shifts produces correct output schema", {
  # Create temporary test data
  test_dir <- tempdir()
  shifts_file <- file.path(test_dir, "test_shifts.csv")
  warming_file <- file.path(test_dir, "test_warming.csv")
  output_dir <- file.path(test_dir, "output")
  
  # Create mock shifts data
  shifts_df <- data.frame(
    species = c("sp1", "sp2", "sp3", "sp4", "sp5"),
    delta_N = c(0.5, 0.7, 0.3, 0.9, 0.4),
    mean_lat = c(45, -30, 60, 10, -60)
  )
  write_csv(shifts_df, shifts_file)
  
  # Create mock warming data
  warming_df <- data.frame(
    species = c("sp1", "sp2", "sp3", "sp4", "sp5"),
    delta_T = c(1.2, 1.5, 0.8, 2.0, 1.0)
  )
  write_csv(warming_df, warming_file)
  
  # Run analysis without phylogeny (WLS fallback)
  result <- analyze_shifts(
    shifts_file = shifts_file,
    warming_file = warming_file,
    phylogeny_file = NULL, # No phylogeny
    output_dir = output_dir
  )
  
  # Check that result is a list with expected fields
  expect_type(result, "list")
  expect_true("slope" %in% names(result))
  expect_true("ci_95_lower" %in% names(result))
  expect_true("ci_95_upper" %in% names(result))
  expect_true("r_squared" %in% names(result))
  expect_true("p_value" %in% names(result))
  expect_equal(result$method, "WLS")
  
  # Check that output files were created
  expect_true(file.exists(file.path(output_dir, "regression_results.csv")))
  
  # Check regression results schema
  results_df <- read_csv(file.path(output_dir, "regression_results.csv"))
  expect_true("slope" %in% names(results_df))
  expect_true("ci_95_lower" %in% names(results_df))
  expect_true("ci_95_upper" %in% names(results_df))
  expect_true("r_squared" %in% names(results_df))
  expect_true("p_value" %in% names(results_df))
  
  # Check regional summary
  expect_true(file.exists(file.path(output_dir, "regional_summary.csv")))
  regional_df <- read_csv(file.path(output_dir, "regional_summary.csv"))
  expect_true("region" %in% names(regional_df))
  expect_true("slope" %in% names(regional_df))
})
