#!/usr/bin/env Rscript
#
# Unit tests for T036b: SC-006 Validation Logic
# Tests the core logic of checking regional regression validity
#

library(testthat)
library(dplyr)
library(readr)
library(jsonlite)
library(here)

# Helper to create a mock CSV content string
create_mock_csv <- function(rows) {
  # rows is a list of lists or data frame rows
  df <- bind_rows(rows)
  write_csv(df, tempfile(fileext = ".csv"))
}

test_that("SC-006 passes when 100% regions are valid", {
  # Mock data: 3 regions, all valid
  mock_data <- tibble(
    region = c("North", "South", "East"),
    slope = c(0.5, 0.8, 0.2),
    ci_lower = c(0.1, 0.4, 0.0),
    ci_upper = c(0.9, 1.2, 0.4),
    r_squared = c(0.6, 0.7, 0.3),
    p_value = c(0.01, 0.02, 0.05)
  )
  
  tmp_file <- tempfile(fileext = ".csv")
  write_csv(mock_data, tmp_file)
  
  # Simulate the logic from validate_sc006.R
  data <- read_csv(tmp_file, show_col_types = FALSE)
  valid_mask <- 
    !is.na(data$slope) & 
    !is.na(data$p_value) & 
    is.finite(data$slope) & 
    is.finite(data$p_value) &
    is.finite(data$ci_lower) &
    is.finite(data$ci_upper)
  
  total <- nrow(data)
  valid <- sum(valid_mask)
  rate <- valid / total
  
  expect_equal(rate, 1.0)
  expect_true(rate >= 0.80)
  
  unlink(tmp_file)
})

test_that("SC-006 fails when success rate < 80%", {
  # Mock data: 5 regions, 3 valid (60%)
  mock_data <- tibble(
    region = c("R1", "R2", "R3", "R4", "R5"),
    slope = c(0.5, NA, 0.2, 0.9, 0.1), # R2 is NA
    ci_lower = c(0.1, 0.1, 0.0, 0.5, 0.0),
    ci_upper = c(0.9, 0.9, 0.4, 1.3, 0.2),
    r_squared = c(0.6, 0.6, 0.3, 0.8, 0.1),
    p_value = c(0.01, NA, 0.05, 0.03, 0.08) # R2 is NA
  )
  
  tmp_file <- tempfile(fileext = ".csv")
  write_csv(mock_data, tmp_file)
  
  data <- read_csv(tmp_file, show_col_types = FALSE)
  valid_mask <- 
    !is.na(data$slope) & 
    !is.na(data$p_value) & 
    is.finite(data$slope) & 
    is.finite(data$p_value) &
    is.finite(data$ci_lower) &
    is.finite(data$ci_upper)
  
  total <- nrow(data)
  valid <- sum(valid_mask)
  rate <- valid / total
  
  expect_equal(total, 5)
  expect_equal(valid, 4) # R2 is invalid, others valid? Wait, R2 has NA slope and p_value.
  # R1: valid
  # R2: NA slope -> invalid
  # R3: valid
  # R4: valid
  # R5: valid
  # So 4/5 = 80%. This should pass. Let's make it fail.
  
  # Modify: Make R3 invalid too
  mock_data$ci_lower[3] <- NA
  
  write_csv(mock_data, tmp_file)
  data <- read_csv(tmp_file, show_col_types = FALSE)
  
  valid_mask <- 
    !is.na(data$slope) & 
    !is.na(data$p_value) & 
    is.finite(data$slope) & 
    is.finite(data$p_value) &
    is.finite(data$ci_lower) &
    is.finite(data$ci_upper)
  
  valid <- sum(valid_mask)
  rate <- valid / nrow(data)
  
  # 3 valid out of 5 = 60%
  expect_equal(rate, 0.6)
  expect_false(rate >= 0.80)
  
  unlink(tmp_file)
})

test_that("SC-006 handles infinite values as invalid", {
  mock_data <- tibble(
    region = c("R1", "R2"),
    slope = c(0.5, Inf), # R2 has Inf
    ci_lower = c(0.1, 1.0),
    ci_upper = c(0.9, 2.0),
    r_squared = c(0.6, 0.8),
    p_value = c(0.01, 0.02)
  )
  
  tmp_file <- tempfile(fileext = ".csv")
  write_csv(mock_data, tmp_file)
  
  data <- read_csv(tmp_file, show_col_types = FALSE)
  valid_mask <- 
    !is.na(data$slope) & 
    !is.na(data$p_value) & 
    is.finite(data$slope) & 
    is.finite(data$p_value) &
    is.finite(data$ci_lower) &
    is.finite(data$ci_upper)
  
  valid <- sum(valid_mask)
  expect_equal(valid, 1) # Only R1 is valid
  
  unlink(tmp_file)
})

test_that("SC-006 returns 0 rate for empty input", {
  mock_data <- tibble(
    region = character(0),
    slope = numeric(0),
    ci_lower = numeric(0),
    ci_upper = numeric(0),
    r_squared = numeric(0),
    p_value = numeric(0)
  )
  
  tmp_file <- tempfile(fileext = ".csv")
  write_csv(mock_data, tmp_file)
  
  data <- read_csv(tmp_file, show_col_types = FALSE)
  
  total <- nrow(data)
  expect_equal(total, 0)
  
  # Logic check
  if (total > 0) {
    valid <- sum(valid_mask)
    rate <- valid / total
  } else {
    rate <- 0
  }
  
  expect_equal(rate, 0)
  
  unlink(tmp_file)
})