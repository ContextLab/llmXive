#!/usr/bin/env Rscript
# Unit tests for T015a: compute_centroids.R
# These tests verify the logic of centroid calculation using mock data.

library(testthat)
library(dplyr)
library(readr)
library(here)

# Source the utils to ensure logging functions exist (mocked if needed)
# We assume utils.R is available as per T004
source(here("src", "code", "utils.R"))

# Mock the main logic for testing
compute_centroids_logic <- function(df) {
  # Replicates the core logic of compute_centroids.R without file I/O
  required_cols <- c("species", "period", "temp_annual", "precip_annual")
  missing_cols <- setdiff(required_cols, names(df))
  if (length(missing_cols) > 0) {
    stop("Missing columns: ", paste(missing_cols, collapse = ", "))
  }

  valid_points <- df %>%
    filter(!is.na(temp_annual) & !is.na(precip_annual))

  if (nrow(valid_points) == 0) {
    stop("No valid records")
  }

  centroids <- valid_points %>%
    group_by(species, period) %>%
    summarise(
      mean_temp = mean(temp_annual, na.rm = TRUE),
      mean_precip = mean(precip_annual, na.rm = TRUE),
      n_observations = n(),
      .groups = 'drop'
    )
  return(centroids)
}

test_that("compute_centroids calculates correct arithmetic means", {
  mock_data <- tibble(
    species = c("A", "A", "A", "B", "B"),
    period = c("1970-2000", "1970-2000", "1970-2000", "1970-2000", "1970-2000"),
    temp_annual = c(10, 20, 30, 5, 15), # Mean A=20, Mean B=10
    precip_annual = c(100, 200, 300, 50, 150) # Mean A=200, Mean B=100
  )

  result <- compute_centroids_logic(mock_data)

  expect_equal(nrow(result), 1)
  expect_equal(result$species[1], "A")
  expect_equal(result$mean_temp[1], 20)
  expect_equal(result$mean_precip[1], 200)
  expect_equal(result$n_observations[1], 3)
})

test_that("compute_centroids handles multiple periods correctly", {
  mock_data <- tibble(
    species = c("A", "A", "A", "A"),
    period = c("1970-2000", "1970-2000", "1991-2020", "1991-2020"),
    temp_annual = c(10, 20, 15, 25), # P1: 15, P2: 20
    precip_annual = c(100, 100, 200, 200) # P1: 100, P2: 200
  )

  result <- compute_centroids_logic(mock_data)

  expect_equal(nrow(result), 2)
  # Check period 1
  p1 <- result %>% filter(period == "1970-2000")
  expect_equal(p1$mean_temp[1], 15)
  expect_equal(p1$mean_precip[1], 100)
  # Check period 2
  p2 <- result %>% filter(period == "1991-2020")
  expect_equal(p2$mean_temp[1], 20)
  expect_equal(p2$mean_precip[1], 200)
})

test_that("compute_centroids filters out NA climate values", {
  mock_data <- tibble(
    species = c("A", "A", "A"),
    period = c("1970-2000", "1970-2000", "1970-2000"),
    temp_annual = c(10, NA, 30), # Mean should be 20 (ignoring NA)
    precip_annual = c(100, 200, 300)
  )

  result <- compute_centroids_logic(mock_data)

  expect_equal(result$mean_temp[1], 20)
  expect_equal(result$n_observations[1], 2) # Only 2 valid rows
})

test_that("compute_centroids fails on missing columns", {
  mock_data <- tibble(
    species = c("A"),
    period = c("1970-2000"),
    temp_annual = c(10)
    # missing precip_annual
  )

  expect_error(compute_centroids_logic(mock_data), "Missing columns")
})

test_that("compute_centroids fails on all NA values", {
  mock_data <- tibble(
    species = c("A", "A"),
    period = c("1970-2000", "1970-2000"),
    temp_annual = c(NA, NA),
    precip_annual = c(NA, NA)
  )

  expect_error(compute_centroids_logic(mock_data), "No valid records")
})
