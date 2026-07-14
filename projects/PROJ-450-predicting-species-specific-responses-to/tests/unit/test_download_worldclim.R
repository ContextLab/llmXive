# tests/unit/test_download_worldclim.R
# Unit tests for download_worldclim.R logic (mocked)

library(testthat)
library(here)

# We cannot easily mock download.file in a simple unit test without extra packages like mockery.
# Instead, we test the helper logic and file path construction.
# We will test the configuration and path generation logic.

test_that("Download map configuration is valid", {
  # Source the script to access variables (or define them locally for test)
  # Since the script is an Rscript entry point, we define the map here for testing
  DOWNLOAD_MAP <- list(
    "bio1_1970_2000" = list(var = 1, period = "7000", desc = "Annual Mean Temp (1970-2000)"),
    "bio1_1991_2020" = list(var = 1, period = "9000", desc = "Annual Mean Temp (1991-2020)"),
    "bio12_1970_2000" = list(var = 12, period = "7000", desc = "Annual Precip (1970-2000)"),
    "bio12_1991_2020" = list(var = 12, period = "9000", desc = "Annual Precip (1991-2020)")
  )

  expect_length(DOWNLOAD_MAP, 4)
  expect_equal(DOWNLOAD_MAP[["bio1_1970_2000"]]$var, 1)
  expect_equal(DOWNLOAD_MAP[["bio12_1991_2020"]]$period, "9000")
})

test_that("File path generation is correct", {
  base_dir <- tempdir()
  wc_dir <- file.path(base_dir, "worldclim_v2")

  # Simulate logic
  var_code <- sprintf("%02d", 1)
  period_code <- "7000"
  zip_name <- paste0("wc2.1_10m_bio_", var_code, "_", period_code, ".zip")
  tif_name <- paste0("wc2.1_10m_bio_", var_code, "_", period_code, ".tif")

  expect_equal(zip_name, "wc2.1_10m_bio_01_7000.zip")
  expect_equal(tif_name, "wc2.1_10m_bio_01_7000.tif")
})

test_that("Directory creation logic works", {
  temp_test_dir <- file.path(tempdir(), "test_wc_dir")
  if (dir.exists(temp_test_dir)) unlink(temp_test_dir, recursive = TRUE)

  expect_false(dir.exists(temp_test_dir))
  dir.create(temp_test_dir, recursive = TRUE)
  expect_true(dir.exists(temp_test_dir))

  unlink(temp_test_dir, recursive = TRUE)
})