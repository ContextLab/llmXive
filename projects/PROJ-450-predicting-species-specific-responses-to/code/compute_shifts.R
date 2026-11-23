#!/usr/bin/env Rscript
# compute_shifts.R
# Task: T021 [US2]
# Description: Perform global z-scoring across ALL species occurrence points pooled
#              and calculate Euclidean distance (ΔN) between periods.
# Input: data/processed/points_with_climate.csv
# Output: data/processed/niche_shifts.csv (species, period_1, period_2, delta_n)

library(dplyr)
library(readr)
library(tidyr)
library(here)

# Source utility functions
source(here("code", "utils.R"))

# Configuration
INPUT_FILE <- here("data", "processed", "points_with_climate.csv")
OUTPUT_FILE <- here("data", "processed", "niche_shifts.csv")
LOG_FILE <- here("logs", "compute_shifts.log")

# Initialize logging
log_message(LOG_FILE, "INFO", "Starting niche shift calculation (T021)")

# Check input file exists
if (!file.exists(INPUT_FILE)) {
  stop(paste("Input file not found:", INPUT_FILE, 
             "- Ensure T015b (compute_centroids) has run successfully."))
}

log_message(LOG_FILE, "INFO", paste("Loading data from:", INPUT_FILE))

# Load the raw occurrence points with climate values
# Expected columns: species, period, temp_c, precip_mm, lon, lat, ...
points_df <- read_csv(INPUT_FILE, show_col_types = FALSE)

log_message(LOG_FILE, "INFO", paste("Loaded", nrow(points_df), "records"))

# Validate required columns
required_cols <- c("species", "period", "temp_c", "precip_mm")
missing_cols <- setdiff(required_cols, names(points_df))
if (length(missing_cols) > 0) {
  stop(paste("Missing required columns in input:", paste(missing_cols, collapse = ", ")))
}

# Handle missing climate values (NA) - log and remove
initial_count <- nrow(points_df)
points_df <- points_df %>%
  filter(!is.na(temp_c) & !is.na(precip_mm))

removed_count <- initial_count - nrow(points_df)
if (removed_count > 0) {
  log_message(LOG_FILE, "WARN", paste("Removed", removed_count, "records with NA climate values"))
}

if (nrow(points_df) == 0) {
  stop("No valid records remaining after NA removal.")
}

# GLOBAL Z-SCORING (FR-005)
# Calculate global mean and SD for temp and precip across ALL species and BOTH periods
log_message(LOG_FILE, "INFO", "Calculating global statistics for z-scoring...")

global_stats <- points_df %>%
  summarise(
    temp_mean = mean(temp_c, na.rm = TRUE),
    temp_sd = sd(temp_c, na.rm = TRUE),
    precip_mean = mean(precip_mm, na.rm = TRUE),
    precip_sd = sd(precip_mm, na.rm = TRUE)
  )

# Check for zero SD (constant variable)
if (global_stats$temp_sd == 0 || global_stats$precip_sd == 0) {
  stop("Global standard deviation is zero for one or more variables. Cannot perform z-scoring.")
}

log_message(LOG_FILE, "INFO", paste("Global Temp: mean =", round(global_stats$temp_mean, 3), 
                                    ", sd =", round(global_stats$temp_sd, 3)))
log_message(LOG_FILE, "INFO", paste("Global Precip: mean =", round(global_stats$precip_mean, 3), 
                                    ", sd =", round(global_stats$precip_sd, 3)))

# Apply global z-scoring
log_message(LOG_FILE, "INFO", "Applying global z-scoring...")

points_z <- points_df %>%
  mutate(
    z_temp = (temp_c - global_stats$temp_mean) / global_stats$temp_sd,
    z_precip = (precip_mm - global_stats$precip_mean) / global_stats$precip_sd
  )

# Pivot to wide format: one row per species, columns for period 1 and period 2 z-scores
# Assuming periods are labeled consistently (e.g., "period_1970_2000", "period_1991_2020")
# We pivot to have: species, z_temp_1, z_temp_2, z_precip_1, z_precip_2

log_message(LOG_FILE, "INFO", "Reshaping data for shift calculation...")

# Determine period names dynamically or assume standard naming
# We will pivot wider based on the 'period' column
points_wide <- points_z %>%
  select(species, period, z_temp, z_precip) %>%
  pivot_wider(
    names_from = period,
    values_from = c(z_temp, z_precip),
    names_sep = "_"
  )

# Calculate Euclidean distance (ΔN) in standardized climate space
# ΔN = sqrt( (z_temp_2 - z_temp_1)^2 + (z_precip_2 - z_precip_1)^2 )
# We need to handle cases where a species might be missing one period
# For this task, we assume both periods exist for the species if it's in the dataset

log_message(LOG_FILE, "INFO", "Calculating Euclidean niche shifts (ΔN)...")

# Identify the column names dynamically
# We expect columns like: z_temp_<period1>, z_temp_<period2>, etc.
# We will filter for rows where both periods are present

# Get unique periods
unique_periods <- unique(points_df$period)
if (length(unique_periods) != 2) {
  stop(paste("Expected exactly 2 periods, found:", length(unique_periods)))
}

# Construct column names
col_temp_1 <- paste0("z_temp_", unique_periods[1])
col_temp_2 <- paste0("z_temp_", unique_periods[2])
col_precip_1 <- paste0("z_precip_", unique_periods[1])
col_precip_2 <- paste0("z_precip_", unique_periods[2])

# Verify columns exist
missing_wide_cols <- setdiff(c(col_temp_1, col_temp_2, col_precip_1, col_precip_2), names(points_wide))
if (length(missing_wide_cols) > 0) {
  stop(paste("Missing expected wide columns:", paste(missing_wide_cols, collapse = ", ")))
}

# Calculate shift
shifts_df <- points_wide %>%
  mutate(
    delta_temp = !!sym(col_temp_2) - !!sym(col_temp_1),
    delta_precip = !!sym(col_precip_2) - !!sym(col_precip_1),
    delta_n = sqrt(delta_temp^2 + delta_precip^2)
  ) %>%
  select(species, delta_n, delta_temp, delta_precip)

log_message(LOG_FILE, "INFO", paste("Calculated shifts for", nrow(shifts_df), "species"))

# Write output
log_message(LOG_FILE, "INFO", paste("Writing output to:", OUTPUT_FILE))

write_csv(shifts_df, OUTPUT_FILE)

log_message(LOG_FILE, "INFO", "Task T021 completed successfully.")

# Print summary to console
cat("Niche shift calculation complete.\n")
cat(paste("Output written to:", OUTPUT_FILE, "\n"))
cat(paste("Species processed:", nrow(shifts_df), "\n"))
cat(paste("Mean shift (ΔN):", round(mean(shifts_df$delta_n), 4), "\n"))
cat(paste("Max shift (ΔN):", round(max(shifts_df$delta_n), 4), "\n"))