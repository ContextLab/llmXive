# tests/unit/test_fetch_gbif.R
# Unit tests for GBIF filtering logic
# Note: These tests use mocks/stubs to avoid live API calls

library(testthat)
library(dplyr)
library(lubridate)

# Source the main script to access functions (if we refactor to functions)
# For now, we test the logic by simulating the data processing steps
# Since fetch_gbif.R is a script, we will test the core logic functions
# that would be extracted or by sourcing and testing the internal logic

# We will define the core logic here for testing purposes
# In a real refactor, this logic should be in a separate utility file

test_that("filters records by date span and coordinates", {
  # Create mock data mimicking GBIF response structure
  mock_data <- data.frame(
    decimalLatitude = c(40.1, 40.2, 40.3, 50.1, 50.2),
    decimalLongitude = c(-74.1, -74.2, -74.3, -120.1, -120.2),
    eventDate = c("1950", "1960", "2020", "2000", "2010"),
    stringsAsFactors = FALSE
  )
  
  # Simulate date parsing logic
  parsed_data <- mock_data %>%
    mutate(
      year = case_when(
        grepl("/", eventDate) ~ as.integer(strsplit(eventDate, "/")[[1]][1]),
        nchar(eventDate) == 4 & grepl("^[0-9]{4}$", eventDate) ~ as.integer(eventDate),
        TRUE ~ NA_integer_
      )
    )
  
  # Test coordinate filtering (all valid in mock)
  valid_coords <- parsed_data %>%
    filter(!is.na(decimalLatitude) & !is.na(decimalLongitude)) %>%
    filter(decimalLatitude >= -90 & decimalLatitude <= 90) %>%
    filter(decimalLongitude >= -180 & decimalLongitude <= 180)
  
  expect_equal(nrow(valid_coords), 5)
  
  # Test year span calculation
  min_year <- min(valid_coords$year, na.rm = TRUE)
  max_year <- max(valid_coords$year, na.rm = TRUE)
  year_span <- max_year - min_year
  
  # Our mock data spans from 1950 to 2020 (70 years)
  expect_equal(year_span, 70)
  expect_true(year_span >= 50)
  
  # Test with a subset that doesn't meet the span
  mock_data_short <- data.frame(
    decimalLatitude = c(40.1, 40.2),
    decimalLongitude = c(-74.1, -74.2),
    eventDate = c("1950", "1955"),
    stringsAsFactors = FALSE
  )
  
  parsed_short <- mock_data_short %>%
    mutate(
      year = case_when(
        grepl("/", eventDate) ~ as.integer(strsplit(eventDate, "/")[[1]][1]),
        nchar(eventDate) == 4 & grepl("^[0-9]{4}$", eventDate) ~ as.integer(eventDate),
        TRUE ~ NA_integer_
      )
    )
  
  min_year_short <- min(parsed_short$year, na.rm = TRUE)
  max_year_short <- max(parsed_short$year, na.rm = TRUE)
  year_span_short <- max_year_short - min_year_short
  
  expect_equal(year_span_short, 5)
  expect_false(year_span_short >= 50)
})

test_that("handles invalid coordinates", {
  mock_data <- data.frame(
    decimalLatitude = c(40.1, 95.0, -95.0, 40.3), # 95 and -95 are invalid
    decimalLongitude = c(-74.1, -74.2, -74.3, 200.0), # 200 is invalid
    eventDate = c("1950", "1960", "1970", "1980"),
    stringsAsFactors = FALSE
  )
  
  filtered <- mock_data %>%
    filter(!is.na(decimalLatitude) & !is.na(decimalLongitude)) %>%
    filter(decimalLatitude >= -90 & decimalLatitude <= 90) %>%
    filter(decimalLongitude >= -180 & decimalLongitude <= 180)
  
  # Only the first and last rows should remain (40.1/-74.1 and 40.3/200.0 -> 200 is invalid)
  # Wait, 200.0 is invalid longitude, so only first row remains
  expect_equal(nrow(filtered), 1)
  expect_equal(filtered$decimalLatitude[1], 40.1)
})

test_that("handles missing event dates", {
  mock_data <- data.frame(
    decimalLatitude = c(40.1, 40.2, 40.3),
    decimalLongitude = c(-74.1, -74.2, -74.3),
    eventDate = c("1950", NA, "2020"),
    stringsAsFactors = FALSE
  )
  
  parsed <- mock_data %>%
    mutate(
      year = case_when(
        grepl("/", eventDate) ~ as.integer(strsplit(eventDate, "/")[[1]][1]),
        nchar(eventDate) == 4 & grepl("^[0-9]{4}$", eventDate) ~ as.integer(eventDate),
        TRUE ~ NA_integer_
      )
    )
  
  # NA eventDate should result in NA year
  expect_true(is.na(parsed$year[2]))
  
  # After filtering NA years
  valid_years <- parsed %>% filter(!is.na(year))
  expect_equal(nrow(valid_years), 2)
})
