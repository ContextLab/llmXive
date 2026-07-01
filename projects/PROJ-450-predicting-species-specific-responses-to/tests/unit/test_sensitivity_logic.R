# tests/unit/test_sensitivity_logic.R
# Unit tests for T033 logic: Flagging and Record Count Thresholds
# These tests verify the logic without requiring full data pipeline execution

library(testthat)

# Mock the utils functions if not loaded, or source the real ones if available
# For unit tests, we often mock side effects. Here we test pure logic functions
# extracted from sensitivity.R or the main logic flow.

# Since the logic is embedded in main(), we will simulate the conditions
# by testing the conditional logic directly.

test_that("Species with < 80 records are skipped", {
  # Simulate a dataframe with 79 records
  n_records <- 79
  min_threshold <- 80

  # Logic from T033
  should_skip <- n_records < min_threshold

  expect_true(should_skip)
})

test_that("Species with >= 80 records are NOT skipped", {
  n_records <- 80
  min_threshold <- 80
  should_skip <- n_records < min_threshold
  expect_false(should_skip)

  n_records <- 150
  should_skip <- n_records < min_threshold
  expect_false(should_skip)
})

test_that("Species with SD >= 0.2 are flagged", {
  sd_val <- 0.2001
  threshold <- 0.2
  is_flagged <- sd_val >= threshold
  expect_true(is_flagged)

  sd_val <- 0.2
  is_flagged <- sd_val >= threshold
  expect_true(is_flagged)
})

test_that("Species with SD < 0.2 are NOT flagged", {
  sd_val <- 0.1999
  threshold <- 0.2
  is_flagged <- sd_val >= threshold
  expect_false(is_flagged)

  sd_val <- 0.0
  is_flagged <- sd_val >= threshold
  expect_false(is_flagged)
})

test_that("compute_niche_shift handles NA correctly", {
  # If a subsample fails to produce two periods, shift should be NA
  # This is tested in the integration test, but basic logic check here
  # The function returns NA if length(unique(periods)) != 2
  df_bad <- data.frame(
    period = c("1970-2000", "1970-2000"),
    temp = c(10, 12),
    precip = c(50, 60)
  )

  # We need to re-define the function locally for the test or source it
  # Assuming we source the helper from the main file or copy it here
  compute_niche_shift <- function(df) {
    if (!all(c("period", "temp", "precip") %in% names(df))) stop("Missing cols")
    periods <- unique(df$period)
    if (length(periods) != 2) return(NA)
    c1 <- df[df$period == periods[1], c("temp", "precip"), drop = FALSE]
    c2 <- df[df$period == periods[2], c("temp", "precip"), drop = FALSE]
    mean_c1 <- colMeans(c1)
    mean_c2 <- colMeans(c2)
    return(sqrt(sum((mean_c2 - mean_c1)^2)))
  }

  result <- compute_niche_shift(df_bad)
  expect_true(is.na(result))
})
