# tests/unit/test_compute_shifts.R
# Unit tests for compute_shifts.R logic
# Tests the core z-scoring and Euclidean distance calculation logic
# using mock data frames to avoid file I/O dependencies.

library(testthat)
library(dplyr)
library(tidyr)

# Source the main script logic (we will wrap the core logic in a function for testing)
# Since compute_shifts.R is a script, we define the core logic here for testing
# In a real refactor, this logic would be extracted to a module.

compute_shifts_logic <- function(df) {
  # 1. Filter NAs
  df_clean <- df %>%
    filter(!is.na(temp_c), !is.na(precip_mm))

  if (nrow(df_clean) == 0) stop("No valid data")

  # 2. Global Stats
  global_stats <- df_clean %>%
    summarise(
      mean_temp = mean(temp_c, na.rm = TRUE),
      sd_temp = sd(temp_c, na.rm = TRUE),
      mean_precip = mean(precip_mm, na.rm = TRUE),
      sd_precip = sd(precip_mm, na.rm = TRUE)
    )

  # 3. Z-score
  if (global_stats$sd_temp == 0) {
    df_clean <- df_clean %>% mutate(temp_z = 0)
  } else {
    df_clean <- df_clean %>%
      mutate(temp_z = (temp_c - global_stats$mean_temp) / global_stats$sd_temp)
  }

  if (global_stats$sd_precip == 0) {
    df_clean <- df_clean %>% mutate(precip_z = 0)
  } else {
    df_clean <- df_clean %>%
      mutate(precip_z = (precip_mm - global_stats$mean_precip) / global_stats$sd_precip)
  }

  # 4. Aggregate
  species_period_means <- df_clean %>%
    group_by(species, period) %>%
    summarise(
      mean_temp_z = mean(temp_z, na.rm = TRUE),
      mean_precip_z = mean(precip_z, na.rm = TRUE),
      .groups = "drop"
    )

  # 5. Wide & Delta
  wide_shifts <- species_period_means %>%
    pivot_wider(
      names_from = period,
      values_from = c(mean_temp_z, mean_precip_z),
      names_sep = "_"
    )

  shifts_result <- wide_shifts %>%
    mutate(
      delta_temp = mean_temp_z_1991_2020 - mean_temp_z_1970_2000,
      delta_precip = mean_precip_z_1991_2020 - mean_precip_z_1970_2000,
      delta_N = sqrt(delta_temp^2 + delta_precip^2)
    )

  return(shifts_result)
}

test_that("Global z-scoring is applied correctly", {
  # Create mock data:
  # Species A: Old period (temp=10, new=20), New period (temp=30)
  # Species B: Old period (temp=10, new=20), New period (temp=30)
  # If we pool them:
  # Old temps: 10, 10 -> mean=10, sd=0 (if only 2 points) -> Edge case
  # Let's make it more robust with 4 points per species

  mock_df <- tibble(
    species = c("A", "A", "A", "A", "B", "B", "B", "B"),
    period = c(rep("1970-2000", 4), rep("1991-2020", 4)),
    temp_c = c(10, 10, 10, 10, 30, 30, 30, 30), # 4 old, 4 new
    precip_mm = c(100, 100, 100, 100, 200, 200, 200, 200)
  )

  result <- compute_shifts_logic(mock_df)

  # Global mean temp = (4*10 + 4*30)/8 = 20
  # Global sd temp = sqrt( (4*(10-20)^2 + 4*(30-20)^2)/7 ) = sqrt(800/7) ~ 10.69
  # Old z = (10-20)/10.69 = -0.935
  # New z = (30-20)/10.69 = 0.935
  # Delta = 0.935 - (-0.935) = 1.87

  expect_equal(nrow(result), 2)
  expect_true(all(result$delta_temp > 0))
})

test_that("Euclidean distance is calculated correctly", {
  # Construct data where we know the exact z-scores
  # Let's force sd=1, mean=0 for simplicity in calculation
  # Old: 0, 0, 0, 0 -> mean=0, sd=0 -> handled by edge case (z=0)
  # Let's use standard normal distribution logic manually

  # Old period: points at z=-1, 1 (mean 0)
  # New period: points at z=1, -1 (mean 0)
  # Delta should be 0? No, wait.
  # Let's try:
  # Old: all points at -1
  # New: all points at 1
  # Delta should be 2.

  # To get z=-1 and z=1 globally, we need data distributed around a mean.
  # Let's create a dataset:
  # Old: 4 points at 0
  # New: 4 points at 2
  # Global: 8 points. Mean = 1.
  # SD = sqrt( (4*(0-1)^2 + 4*(2-1)^2)/7 ) = sqrt(8/7) ~ 1.069
  # Old z = (0-1)/1.069 = -0.935
  # New z = (2-1)/1.069 = 0.935
  # Delta = 1.87

  mock_df <- tibble(
    species = c("A", "A", "A", "A", "B", "B", "B", "B"),
    period = c(rep("1970-2000", 4), rep("1991-2020", 4)),
    temp_c = c(0, 0, 0, 0, 2, 2, 2, 2),
    precip_mm = c(0, 0, 0, 0, 0, 0, 0, 0) # Precip constant -> z=0
  )

  result <- compute_shifts_logic(mock_df)

  # Check delta_N
  # Since precip change is 0, delta_N should equal abs(delta_temp)
  expect_equal(result$delta_N[1], abs(result$delta_temp[1]), tolerance = 0.001)
})

test_that("Function handles NA values correctly", {
  mock_df <- tibble(
    species = c("A", "A", "A"),
    period = c("1970-2000", "1970-2000", "1991-2020"),
    temp_c = c(10, NA, 20),
    precip_mm = c(100, 100, 200)
  )

  result <- compute_shifts_logic(mock_df)

  # Should drop the NA row and calculate on remaining 2
  expect_equal(nrow(result), 1)
})

test_that("Function throws error on empty data", {
  mock_df <- tibble(
    species = character(0),
    period = character(0),
    temp_c = numeric(0),
    precip_mm = numeric(0)
  )

  expect_error(compute_shifts_logic(mock_df), "No valid data")
})