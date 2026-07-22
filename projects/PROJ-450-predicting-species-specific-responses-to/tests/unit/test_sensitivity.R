# tests/unit/test_sensitivity.R
# Unit tests for sensitivity analysis logic (T028, T029)
#
# Tests:
# - Subsampling logic (random selection with seed)
# - SD calculation and flagging logic (>= 0.2 threshold)

library(testthat)
library(dplyr)
library(tidyr)

# Source the main script to access helper functions
# Note: In a real setup, helper functions should be in a separate utils file
# For this test, we source the script directly or define the helper here
source(here::here("src", "code", "sensitivity.R"))

# Mock data for testing
create_mock_points <- function(n = 100, period = "1970-2000") {
  data.frame(
    species = "TestSpecies",
    period = period,
    temp = rnorm(n, mean = 15, sd = 2),
    precip = rnorm(n, mean = 1000, sd = 200),
    stringsAsFactors = FALSE
  )
}

describe("compute_niche_shift", {
  it("calculates Euclidean distance correctly", {
    # Create mock data for two periods
    p1 <- create_mock_points(n = 50, period = "1970-2000")
    p2 <- create_mock_points(n = 50, period = "1991-2020")
    # Shift the second period to create a known distance
    p2$temp <- p2$temp + 1  # +1 degree shift
    p2$precip <- p2$precip + 100  # +100mm shift

    combined <- bind_rows(p1, p2)
    shift_val <- compute_niche_shift(combined)

    # Expected distance: sqrt(1^2 + 100^2) approx 100.005
    expect_true(!is.na(shift_val))
    expect_gt(shift_val, 100)
    expect_lt(shift_val, 101)
  })

  it("returns NA if one period is missing", {
    p1 <- create_mock_points(n = 50, period = "1970-2000")
    # No second period
    shift_val <- compute_niche_shift(p1)
    expect_true(is.na(shift_val))
  })
})

describe("subsample logic", {
  it("selects exactly 50% of records with set.seed", {
    set.seed(42)
    df <- create_mock_points(n = 100, period = "1970-2000")
    n_total <- nrow(df)
    n_sample <- floor(n_total * 0.5)

    indices <- sample(1:n_total, size = n_sample)
    sampled_df <- df[indices, ]

    expect_equal(nrow(sampled_df), n_sample)
    # Verify randomness by checking if indices are not sequential
    expect_false(all(indices == 1:n_sample))
  })

  it("produces reproducible results with set.seed(42)", {
    set.seed(42)
    df <- create_mock_points(n = 100, period = "1970-2000")
    indices1 <- sample(1:nrow(df), size = floor(nrow(df) * 0.5))

    set.seed(42)
    indices2 <- sample(1:nrow(df), size = floor(nrow(df) * 0.5))

    expect_equal(indices1, indices2)
  })
})

describe("flagging logic", {
  it("flags species with SD >= 0.2", {
    shifts <- c(1.0, 1.1, 1.2, 1.3, 1.4) # SD approx 0.158 -> not flagged
    sd_val <- sd(shifts)
    is_flagged <- sd_val >= 0.2
    expect_false(is_flagged)

    shifts_high <- c(1.0, 1.0, 2.0, 2.0, 3.0) # SD approx 0.707 -> flagged
    sd_val_high <- sd(shifts_high)
    is_flagged_high <- sd_val_high >= 0.2
    expect_true(is_flagged_high)
  })
})
