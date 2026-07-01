#!/usr/bin/env Rscript
# T002: Tests for dependency installation and project initialization
# This test verifies that the required packages can be loaded and that 
# the basic project structure (renv) is initialized.

library(testthat)

test_that("required packages are installed and loadable", {
  required_packages <- c(
    "rgbif", "raster", "sf", "ggplot2", "dplyr", 
    "tidyr", "caper", "phylolm", "pwr", "tibble", 
    "lubridate", "here", "testthat"
  )
  
  for (pkg in required_packages) {
    expect_true(
      requireNamespace(pkg, quietly = TRUE),
      info = paste("Package", pkg, "should be installed.")
    )
  }
})

test_that("renv is initialized in the project root", {
  # Check if renv.lock exists in the parent directory (project root)
  renv_lockfile <- file.path("..", "renv.lock")
  expect_true(
    file.exists(renv_lockfile),
    info = "renv.lock should exist in the project root."
  )
})

test_that("here package resolves project root correctly", {
  skip_if_not(requireNamespace("here", quietly = TRUE))
  
  # The project root should be the parent of src/code
  expected_root <- normalizePath("..", winslash = "/")
  actual_root <- here::here()
  
  # Check if the normalized paths match
  expect_equal(
    normalizePath(actual_root, winslash = "/"),
    expected_root,
    info = "here::here() should resolve to the project root."
  )
})

test_that("stringsAsFactors option is set correctly", {
  # This test assumes the .Rprofile has been sourced or R started with it
  # If running via script, we check the option directly
  expect_false(
    getOption("stringsAsFactors"),
    info = "stringsAsFactors should be FALSE."
  )
})

# Run tests if executed directly
if (!interactive()) {
  test_file <- testthat::test_package("test_install_deps")
}