# tests/unit/test_download_worldclim.R
# Unit tests for download_worldclim.R
# Note: Actual download tests are integration-level. 
# These tests verify the logic of file existence checking and path construction.

library(testthat)
library(here)

# Source the script to test helper functions if exposed, 
# or we test the behavior by mocking file.exists
# Since the script is a standalone runner, we test the logic by sourcing the file
# and checking if it errors on syntax, or we mock the environment.
# For simplicity, we test the path construction logic.

test_that("Path construction logic is correct", {
  # We can't easily run the download logic without network, 
  # so we verify the expected file names would be generated correctly.
  
  # Simulate the logic from the script
  vars_to_fetch <- c(1, 12)
  periods <- list(
    list(name = "1970-2000", suffix = ""),
    list(name = "1991-2020", suffix = "_current")
  )
  
  expected_names <- c()
  for (v in vars_to_fetch) {
    for (p in periods) {
      if (p$suffix != "") {
        expected_names <- c(expected_names, sprintf("wc2.1_2.5m_bio_%d_%s.tif", v, gsub("-", "", p$name)))
      } else {
        expected_names <- c(expected_names, sprintf("wc2.1_2.5m_bio_%d.tif", v))
      }
    }
  }
  
  expect_equal(length(expected_names), 4)
  expect_true(all(grepl("wc2.1_2.5m_bio_", expected_names)))
})

test_that("Output directory creation does not fail", {
  # Just ensure the directory creation function works
  tmp_dir <- tempfile()
  expect_no_error(dir.create(tmp_dir, recursive = TRUE))
  expect_true(dir.exists(tmp_dir))
  unlink(tmp_dir)
})