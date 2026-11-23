#!/usr/bin/env Rscript

# compute_shifts.R
# Implements US2: Global z-scoring and Euclidean niche shift calculation (ΔN)
# Input: data/processed/points_with_climate.csv (produced by T015b)
# Output: data/processed/shifts.csv (species, period, temp_z, precip_z, delta_N)
#
# FR-005: Standardize climate variables globally across ALL species occurrence points
#         before calculating per-species shifts.

library(dplyr)
library(tidyr)
library(readr)
library(here)

# Source utility functions (logging, validation)
source(here("src", "code", "utils.R"))

log_info("Starting niche shift computation (T021)...")

# Define paths
input_path <- here("data", "processed", "points_with_climate.csv")
output_path <- here("data", "processed", "shifts.csv")

# Verify input exists
if (!file.exists(input_path)) {
  log_error(paste("Input file not found:", input_path))
  log_error("Prerequisite T015b (compute_centroids.R) must be run first to generate points_with_climate.csv")
  stop("Missing input file: points_with_cimate.csv")
}

log_info(paste("Loading data from:", input_path))
df <- read_csv(input_path, show_col_types = FALSE)

# Validate required columns
required_cols <- c("species", "period", "temp_c", "precip_mm")
missing_cols <- setdiff(required_cols, names(df))
if (length(missing_cols) > 0) {
  log_error(paste("Missing required columns:", paste(missing_cols, collapse = ", ")))
  stop("Input data missing required columns")
}

# Filter out rows with NA in climate variables (cannot z-score NA)
initial_count <- nrow(df)
df_clean <- df %>%
  filter(!is.na(temp_c), !is.na(precip_mm))

dropped_count <- initial_count - nrow(df_clean)
if (dropped_count > 0) {
  log_warning(paste("Dropped", dropped_count, "rows with NA climate values."))
}

if (nrow(df_clean) == 0) {
  log_error("No valid data points remaining after NA filtering.")
  stop("Cannot compute shifts: no valid data.")
}

log_info("Performing GLOBAL z-scoring across all species and periods...")

# Calculate global mean and SD for temperature and precip
# This standardizes the entire dataset together, not per species/period
global_stats <- df_clean %>%
  summarise(
    mean_temp = mean(temp_c, na.rm = TRUE),
    sd_temp = sd(temp_c, na.rm = TRUE),
    mean_precip = mean(precip_mm, na.rm = TRUE),
    sd_precip = sd(precip_mm, na.rm = TRUE)
  )

# Handle edge case where SD is 0 (constant variable) - though unlikely in real climate data
if (global_stats$sd_temp == 0) {
  log_warning("Global temperature SD is 0. Setting z-score to 0 for all.")
  df_clean <- df_clean %>% mutate(temp_z = 0)
} else {
  df_clean <- df_clean %>%
    mutate(temp_z = (temp_c - global_stats$mean_temp) / global_stats$sd_temp)
}

if (global_stats$sd_precip == 0) {
  log_warning("Global precip SD is 0. Setting z-score to 0 for all.")
  df_clean <- df_clean %>% mutate(precip_z = 0)
} else {
  df_clean <- df_clean %>%
    mutate(precip_z = (precip_mm - global_stats$mean_precip) / global_stats$sd_precip)
}

log_info("Calculating per-species mean z-scores per period...")

# Aggregate to species x period level (mean of z-scores)
species_period_means <- df_clean %>%
  group_by(species, period) %>%
  summarise(
    mean_temp_z = mean(temp_z, na.rm = TRUE),
    mean_precip_z = mean(precip_z, na.rm = TRUE),
    n_points = n(),
    .groups = "drop"
  )

# Pivot to wide format to calculate Euclidean distance
# Periods are expected to be "1970-2000" and "1991-2020"
wide_shifts <- species_period_means %>%
  pivot_wider(
    names_from = period,
    values_from = c(mean_temp_z, mean_precip_z),
    names_sep = "_"
  )

# Calculate Euclidean distance (ΔN)
# ΔN = sqrt( (z_temp_new - z_temp_old)^2 + (z_precip_new - z_precip_old)^2 )
shifts_result <- wide_shifts %>%
  mutate(
    delta_temp = mean_temp_z_1991_2020 - mean_temp_z_1970_2000,
    delta_precip = mean_precip_z_1991_2020 - mean_precip_z_1970_2000,
    delta_N = sqrt(delta_temp^2 + delta_precip^2)
  ) %>%
  select(species, delta_temp, delta_precip, delta_N, mean_temp_z_1970_2000, mean_precip_z_1970_2000,
         mean_temp_z_1991_2020, mean_precip_z_1991_2020)

# Ensure output directory exists
output_dir <- dirname(output_path)
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
  log_info(paste("Created output directory:", output_dir))
}

# Write output
write_csv(shifts_result, output_path)
log_info(paste("Successfully wrote shifts to:", output_path))
log_info(paste("Total species with shift calculated:", nrow(shifts_result)))

# Log summary stats
log_info(paste("Mean ΔN:", round(mean(shifts_result$delta_N, na.rm = TRUE), 4)))
log_info(paste("Max ΔN:", round(max(shifts_result$delta_N, na.rm = TRUE), 4)))
log_info("Niche shift computation (T021) completed.")
