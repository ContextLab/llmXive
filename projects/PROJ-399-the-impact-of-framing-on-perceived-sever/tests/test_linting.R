# Test suite for linting configuration
# This test verifies that the linting setup is working correctly

library(testthat)

# Skip tests if lintr is not available
skip_if_not_installed("lintr")

test_that("lintr configuration file exists", {
  expect_true(file.exists("code/.lintr"))
})

test_that("R profile exists and loads correctly", {
  expect_true(file.exists("code/.Rprofile"))
  
  # Try to source the R profile
  expect_silent(source("code/.Rprofile", local = TRUE))
})

test_that("linting helper function is available", {
  # Source the profile to get helper functions
  source("code/.Rprofile", local = TRUE)
  
  expect_true(exists("run_lint"))
  expect_true(is.function(run_lint))
})

test_that("format helper function is available", {
  source("code/.Rprofile", local = TRUE)
  
  expect_true(exists("format_code"))
  expect_true(is.function(format_code))
})

test_that("basic R files pass linting", {
  # Test a simple R file
  test_file <- tempfile(fileext = ".R")
  writeLines(c(
    "# Test file",
    "x <- 1 + 2",
    "y <- x * 3"
  ), test_file)
  
  # Run lints on the test file
  results <- lintr::lint(test_file)
  
  # Should have no errors (warnings are OK)
  expect_true(length(results) == 0 || all(sapply(results, function(r) r$type == "warning")))
  
  # Clean up
  unlink(test_file)
})

test_that("project linters are configured correctly", {
  source("code/.Rprofile", local = TRUE)
  
  # Check that lintr is loaded
  expect_true(requireNamespace("lintr", quietly = TRUE))
  
  # Check that styler is available
  expect_true(requireNamespace("styler", quietly = TRUE))
})

test_that("linting rules match configuration", {
  # Verify some key linting rules are active
  config <- lintr::read_settings("code/.lintr")
  
  expect_equal(config$indent_by, 2)
  expect_equal(config$line_length, 100)
  expect_true(config$allow_single_quotes == FALSE)
})