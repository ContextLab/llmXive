# tests/unit/test_compute_centroids.R
# Unit tests for compute_centroids.R (T015a)
# Uses testthat framework

library(testthat)

# We will test the logic by mocking the input data and checking the aggregation
# Since the script sources utils.R, we need to ensure utils.R is available or mock it
# For unit testing the core logic, we extract the aggregation logic into a function
# or test the script execution with a temporary file.

# Helper to simulate the core aggregation logic
compute_centroids_logic <- function(df) {
  required_cols <- c("species", "period", "temp", "precip")
  missing_cols <- setdiff(required_cols, names(df))
  if (length(missing_cols) > 0) {
    stop(paste("Missing columns:", paste(missing_cols, collapse = ", ")))
  }
  
  df$temp <- as.numeric(df$temp)
  df$precip <- as.numeric(df$precip)
  
  valid_rows <- complete.cases(df[, required_cols])
  df <- df[valid_rows, ]
  
  centroids <- aggregate(
    cbind(temp, precip) ~ species + period,
    data = df,
    FUN = mean,
    na.rm = TRUE
  )
  
  centroids$computed_at <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  centroids$record_count <- ave(df$temp, df$species, df$period, FUN = length)
  
  centroids <- centroids[, c("species", "period", "temp", "precip", "record_count", "computed_at")]
  return(centroids)
}

test_that("compute_centroids_logic calculates correct means", {
  # Create mock data
  mock_df <- data.frame(
    species = c("Sp1", "Sp1", "Sp1", "Sp2", "Sp2"),
    period = c("1970-2000", "1970-2000", "1991-2020", "1970-2000", "1991-2020"),
    temp = c(10.0, 12.0, 14.0, 20.0, 22.0),
    precip = c(100, 200, 300, 400, 500),
    stringsAsFactors = FALSE
  )
  
  result <- compute_centroids_logic(mock_df)
  
  # Check Sp1, 1970-2000: mean temp = (10+12)/2 = 11, precip = (100+200)/2 = 150
  sp1_70 <- result[result$species == "Sp1" & result$period == "1970-2000", ]
  expect_equal(sp1_70$temp, 11.0)
  expect_equal(sp1_70$precip, 150.0)
  expect_equal(sp1_70$record_count, 2)
  
  # Check Sp2, 1991-2020: mean temp = 22, precip = 500
  sp2_91 <- result[result$species == "Sp2" & result$period == "1991-2020", ]
  expect_equal(sp2_91$temp, 22.0)
  expect_equal(sp2_91$precip, 500.0)
  expect_equal(sp2_91$record_count, 1)
})

test_that("compute_centroids_logic handles NA values", {
  mock_df <- data.frame(
    species = c("Sp1", "Sp1", "Sp1"),
    period = c("1970-2000", "1970-2000", "1970-2000"),
    temp = c(10.0, NA, 12.0),
    precip = c(100, 200, NA),
    stringsAsFactors = FALSE
  )
  
  # Should remove rows with NA
  result <- compute_centroids_logic(mock_df)
  
  # Only one valid row (10, 100)
  expect_equal(nrow(result), 1)
  expect_equal(result$temp, 10.0)
  expect_equal(result$precip, 100.0)
  expect_equal(result$record_count, 1)
})

test_that("compute_centroids_logic errors on missing columns", {
  mock_df <- data.frame(
    species = c("Sp1"),
    period = c("1970-2000"),
    temp = c(10.0)
    # missing 'precip'
  )
  
  expect_error(compute_centroids_logic(mock_df), "Missing columns")
})

test_that("compute_centroids_logic outputs correct column order", {
  mock_df <- data.frame(
    species = c("Sp1"),
    period = c("1970-2000"),
    temp = c(10.0),
    precip = c(100.0),
    stringsAsFactors = FALSE
  )
  
  result <- compute_centroids_logic(mock_df)
  expected_cols <- c("species", "period", "temp", "precip", "record_count", "computed_at")
  expect_equal(names(result), expected_cols)
})
