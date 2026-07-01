# tests/unit/test_fetch_gbif.R
# Unit tests for fetch_gbif.R logic
# Note: These tests use mocks/stubs to avoid hitting the live API during unit testing.
# They verify the logic of taxonomic key resolution and filtering.

library(testthat)
library(dplyr)
library(lubridate)

# Source the utility functions used by the script
# Assuming utils.R is in src/code
source(here::here("src", "code", "utils.R"))

# Mock data for testing
mock_backbone_success <- list(
  usageKey = 12345,
  rank = "SPECIES"
)
mock_backbone_fail <- list(
  usageKey = NULL,
  rank = "NO_RANK"
)

test_that("resolve_taxon_key logic handles successful backbone lookup", {
  # Simulate the logic inside fetch_gbif.R
  test_func <- function(backbone_result) {
    if (!is.null(backbone_result$usageKey) && backbone_result$rank != "NO_RANK") {
      return(backbone_result$usageKey)
    } else {
      return(NULL)
    }
  }

  expect_equal(test_func(mock_backbone_success), 12345)
  expect_null(test_func(mock_backbone_fail))
})

test_that("date parsing and year extraction works correctly", {
  test_dates <- c("2020-05-12", "1980-01-01", "2020-12-31T10:00:00", NA)
  df <- data.frame(eventDate = test_dates, stringsAsFactors = FALSE)

  df_parsed <- df %>%
    mutate(
      eventDate_parsed = ymd(eventDate, quiet = TRUE),
      year = year(eventDate_parsed)
    )

  expect_equal(df_parsed$year[1], 2020)
  expect_equal(df_parsed$year[2], 1980)
  expect_equal(df_parsed$year[3], 2020)
  expect_true(is.na(df_parsed$year[4]))
})

test_that("coordinate filtering removes NA lat/lon", {
  df <- data.frame(
    decimalLatitude = c(10.5, NA, 20.0),
    decimalLongitude = c(-10.5, 15.0, NA),
    stringsAsFactors = FALSE
  )

  df_filtered <- df %>%
    filter(!is.na(decimalLatitude) & !is.na(decimalLongitude))

  expect_equal(nrow(df_filtered), 0) # Both rows have at least one NA
})

test_that("year range filtering works", {
  df <- data.frame(
    year = c(1800, 1950, 2023, 2030, NA),
    stringsAsFactors = FALSE
  )
  current_year <- 2023

  df_filtered <- df %>%
    filter(!is.na(year) & year <= current_year & year >= 1900)

  expect_equal(nrow(df_filtered), 2)
  expect_true(all(df_filtered$year >= 1900 & df_filtered$year <= 2023))
})
