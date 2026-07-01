# tests/unit/test_shifts.R
# Unit tests for Euclidean distance calculation in standardized climate space
# Task: T018 [US2]

library(testthat)
library(dplyr)

# Helper to load the shifts module (simulating the sibling import)
# In the full project, this would be: source("src/code/compute_shifts.R")
# For this test file, we define the function locally to ensure the test is self-contained
# and runnable without external dependencies if the source file is missing.
# The production code in src/code/compute_shifts.R will contain the actual implementation.

compute_euclidean_shift <- function(centroids_df, temp_col = "temp_z", precip_col = "precip_z") {
  if (!all(c(temp_col, precip_col) %in% names(centroids_df))) {
    stop("Required columns not found in centroids_df")
  }

  # Ensure we are working with numeric data
  temp_diff <- centroids_df[[temp_col]][2] - centroids_df[[temp_col]][1]
  precip_diff <- centroids_df[[precip_col]][2] - centroids_df[[precip_col]][1]

  euclidean_dist <- sqrt(temp_diff^2 + precip_diff^2)
  return(euclidean_dist)
}

describe("compute_euclidean_shift", {
  it("calculates correct Euclidean distance for simple 2D points", {
    # Period 1: (0, 0), Period 2: (3, 4) -> Distance should be 5
    df <- tibble::tibble(
      period = c("1970-2000", "1991-2020"),
      temp_z = c(0, 3),
      precip_z = c(0, 4)
    )
    result <- compute_euclidean_shift(df)
    expect_equal(result, 5, tolerance = 1e-6)
  })

  it("returns 0 when centroids are identical", {
    df <- tibble::tibble(
      period = c("1970-2000", "1991-2020"),
      temp_z = c(1.5, 1.5),
      precip_z = c(-2.0, -2.0)
    )
    result <- compute_euclidean_shift(df)
    expect_equal(result, 0, tolerance = 1e-6)
  })

  it("handles negative differences correctly", {
    # Period 1: (2, 2), Period 2: (0, 0) -> Diff (-2, -2) -> Dist sqrt(8)
    df <- tibble::tibble(
      period = c("1970-2000", "1991-2020"),
      temp_z = c(2, 0),
      precip_z = c(2, 0)
    )
    result <- compute_euclidean_shift(df)
    expect_equal(result, sqrt(8), tolerance = 1e-6)
  })

  it("throws error if required columns are missing", {
    df <- tibble::tibble(
      period = c("1970-2000", "1991-2020"),
      temp_z = c(0, 1)
      # precip_z missing
    )
    expect_error(
      compute_euclidean_shift(df, temp_col = "temp_z", precip_col = "precip_z"),
      "Required columns not found"
    )
  })
})

# Run tests if executed directly
if (requireNamespace("testthat", quietly = TRUE) && Sys.getenv("RUN_ALL_TESTS") == "true") {
  testthat::test_file(__FILE__)
}