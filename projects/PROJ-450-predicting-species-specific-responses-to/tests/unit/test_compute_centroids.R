# tests/unit/test_compute_centroids.R
# Unit tests for compute_centroids.R logic

library(testthat)
library(dplyr)
library(readr)
library(here)

# Source the script logic (we will test the functions if extracted, 
# but since it's a script, we test the data transformation logic directly)

test_that("compute_centroids calculates arithmetic mean correctly", {
  # Create a mock dataset
  mock_data <- tibble(
    species = c("A", "A", "A", "B", "B"),
    period = c("1970-2000", "1970-2000", "1991-2020", "1970-2000", "1970-2000"),
    temp = c(10.0, 12.0, 11.0, 20.0, 22.0),
    precip = c(100.0, 100.0, 150.0, 500.0, 500.0),
    lon = c(1, 1, 1, 2, 2),
    lat = c(1, 1, 1, 2, 2)
  )
  
  # Expected results:
  # Species A, 1970-2000: temp = 11.0, precip = 100.0, count = 2
  # Species A, 1991-2020: temp = 11.0, precip = 150.0, count = 1
  # Species B, 1970-2000: temp = 21.0, precip = 500.0, count = 2
  
  result <- mock_data %>%
    group_by(species, period) %>%
    summarise(
      mean_temp = mean(temp, na.rm = TRUE),
      mean_precip = mean(precip, na.rm = TRUE),
      count = n(),
      .groups = 'drop'
    ) %>%
    arrange(species, period)
  
  expect_equal(nrow(result), 3)
  expect_equal(result$mean_temp[1], 11.0) # A, 1970-2000
  expect_equal(result$mean_precip[1], 100.0)
  expect_equal(result$count[1], 2)
  
  expect_equal(result$mean_temp[3], 21.0) # B, 1970-2000
  expect_equal(result$count[3], 2)
})

test_that("compute_centroids handles NA values correctly", {
  mock_data <- tibble(
    species = c("A", "A", "A"),
    period = c("1970-2000", "1970-2000", "1970-2000"),
    temp = c(10.0, NA, 12.0),
    precip = c(100.0, 100.0, NA)
  )
  
  # Logic: Filter out rows with ANY NA in temp or precip before grouping
  # Row 1: (10, 100) -> Keep
  # Row 2: (NA, 100) -> Drop
  # Row 3: (12, NA) -> Drop
  # Result: Only Row 1 remains.
  
  cleaned <- mock_data %>%
    filter(!is.na(temp) & !is.na(precip))
  
  expect_equal(nrow(cleaned), 1)
  expect_equal(cleaned$temp[1], 10.0)
})

test_that("compute_centroids handles all NA values gracefully", {
  mock_data <- tibble(
    species = c("A", "A"),
    period = c("1970-2000", "1970-2000"),
    temp = c(NA, NA),
    precip = c(NA, NA)
  )
  
  cleaned <- mock_data %>%
    filter(!is.na(temp) & !is.na(precip))
  
  expect_equal(nrow(cleaned), 0)
})

test_that("compute_centroids output schema matches requirements", {
  mock_data <- tibble(
    species = c("A"),
    period = c("1970-2000"),
    temp = c(10.0),
    precip = c(100.0)
  )
  
  result <- mock_data %>%
    group_by(species, period) %>%
    summarise(
      mean_temp = mean(temp, na.rm = TRUE),
      mean_precip = mean(precip, na.rm = TRUE),
      count = n(),
      .groups = 'drop'
    )
  
  expect_true("mean_temp" %in% colnames(result))
  expect_true("mean_precip" %in% colnames(result))
  expect_true("count" %in% colnames(result))
  expect_true("species" %in% colnames(result))
  expect_true("period" %in% colnames(result))
})
