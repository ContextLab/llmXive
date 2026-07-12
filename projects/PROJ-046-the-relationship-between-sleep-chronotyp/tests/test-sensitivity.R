#!/usr/bin/env Rscript
# T027: Unit Test for Sensitivity Analysis Output
# Verifies that the sensitivity sweep file exists and contains expected columns.

library(testthat)
library(readr)

test_that("Sensitivity sweep file exists", {
  expect_true(file.exists("data/derived/sensitivity_sweep.csv"), 
              info = "Sensitivity sweep file not found")
})

test_that("Sensitivity sweep has required columns", {
  if (file.exists("data/derived/sensitivity_sweep.csv")) {
    df <- read_csv("data/derived/sensitivity_sweep.csv", show_col_types = FALSE)
    expect_true("subscale" %in% names(df))
    expect_true("alpha_threshold" %in% names(df))
    expect_true("p_value" %in% names(df))
    expect_true("significant" %in% names(df))
  }
})

test_that("Sensitivity sweep has correct alpha thresholds", {
  if (file.exists("data/derived/sensitivity_sweep.csv")) {
    df <- read_csv("data/derived/sensitivity_sweep.csv", show_col_types = FALSE)
    expected_thresholds <- c(0.01, 0.0125, 0.015)
    found_thresholds <- unique(df$alpha_threshold)
    expect_true(all(expected_thresholds %in% found_thresholds))
  }
})

test_that("Significant column is boolean", {
  if (file.exists("data/derived/sensitivity_sweep.csv")) {
    df <- read_csv("data/derived/sensitivity_sweep.csv", show_col_types = FALSE)
    expect_s3_class(df$significant, "logical")
  }
})

test_that("P-values are numeric and between 0 and 1", {
  if (file.exists("data/derived/sensitivity_sweep.csv")) {
    df <- read_csv("data/derived/sensitivity_sweep.csv", show_col_types = FALSE)
    expect_true(all(df$p_value >= 0 & df$p_value <= 1, na.rm = TRUE))
  }
})
