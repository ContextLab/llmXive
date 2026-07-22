#!/usr/bin/env Rscript
# sensitivity.R
# User Story 3: Sensitivity Analysis of Sampling Effort
#
# This script performs a subsampling sensitivity analysis on occurrence records.
# It subsamples 50% of records per species (10 replicates), recomputes niche shift
# magnitudes, calculates mean/SD, and flags high-variability species.
#
# Inputs:
#   - data/raw/occurrences.csv (Raw GBIF records from T013)
#   - data/processed/points_with_climate.csv (Points with climate values from T015b)
#   - data/processed/centroids.csv (Centroids from T015a)
#
# Outputs:
#   - results/sensitivity_summary.csv (Summary statistics per species)
#   - Appends to logs/sensitivity.log
#
# Requirements:
#   - set.seed(42) for reproducibility
#   - 50% subsample, 10 replicates
#   - Skip species with <80 records
#   - Flag species with SD >= 0.2
#   - FR-009: Reproducibility
#   - FR-010: Logging

library(dplyr)
library(tidyr)
library(readr)
library(here)
source(here("src", "code", "utils.R"))

# --- Configuration ---
N_REPLICATES <- 10
SUBSAMPLE_RATIO <- 0.5
MIN_RECORDS <- 80
SD_THRESHOLD <- 0.2
SEED_VAL <- 42

# --- Paths ---
RAW_DATA_PATH <- here("data", "raw", "occurrences.csv")
POINTS_WITH_CLIMATE_PATH <- here("data", "processed", "points_with_climate.csv")
CENTROIDS_PATH <- here("data", "processed", "centroids.csv")
OUTPUT_SUMMARY_PATH <- here("results", "sensitivity_summary.csv")
LOG_FILE_PATH <- here("logs", "sensitivity.log")

# --- Helper Functions ---

compute_niche_shift <- function(points_df, period_col = "period", temp_col = "temp", precip_col = "precip") {
  # Computes Euclidean distance between centroids of two periods
  # Input: points_df with columns for period, temp, precip
  if (!all(c(period_col, temp_col, precip_col) %in% names(points_df))) {
    stop("Missing required columns in points_df")
  }

  # Calculate centroids per period
  centroids <- points_df %>%
    group_by(.data[[period_col]]) %>%
    summarise(
      temp_mean = mean(.data[[temp_col]], na.rm = TRUE),
      precip_mean = mean(.data[[precip_col]], na.rm = TRUE),
      .groups = 'drop'
    )

  # Ensure we have both periods
  if (nrow(centroids) < 2) {
    return(NA_real_)
  }

  # Calculate Euclidean distance
  p1 <- centroids %>% filter(.data[[period_col]] == "1970-2000")
  p2 <- centroids %>% filter(.data[[period_col]] == "1991-2020")

  if (nrow(p1) == 0 || nrow(p2) == 0) {
    return(NA_real_)
  }

  dist_val <- sqrt((p1$temp_mean - p2$temp_mean)^2 + (p1$precip_mean - p2$precip_mean)^2)
  return(dist_val)
}

# --- Main Execution ---

main <- function() {
  # Initialize logging
  log_info(LOG_FILE_PATH, "Starting sensitivity analysis (T034)")

  # Check input files
  if (!file.exists(RAW_DATA_PATH)) {
    log_error(LOG_FILE_PATH, paste("Raw data file not found:", RAW_DATA_PATH))
    stop("Raw data file not found. Please run T013 first.")
  }

  if (!file.exists(POINTS_WITH_CLIMATE_PATH)) {
    log_error(LOG_FILE_PATH, paste("Points with climate file not found:", POINTS_WITH_CLIMATE_PATH))
    stop("Points with climate file not found. Please run T015b first.")
  }

  # Load data
  log_info(LOG_FILE_PATH, "Loading raw occurrence data")
  raw_data <- read_csv(RAW_DATA_PATH, col_types = cols())

  log_info(LOG_FILE_PATH, "Loading points with climate data")
  points_data <- read_csv(POINTS_WITH_CLIMATE_PATH, col_types = cols())

  # Ensure 'period' column is present in points_data (should be from T015b)
  if (!"period" %in% names(points_data)) {
    log_error(LOG_FILE_PATH, "Missing 'period' column in points_with_climate.csv")
    stop("Missing 'period' column in points_with_climate.csv")
  }

  # Group by species
  species_list <- unique(points_data$species)
  log_info(LOG_FILE_PATH, paste("Processing", length(species_list), "species"))

  results_list <- list()
  skipped_species <- list()
  flagged_species <- list()

  set.seed(SEED_VAL)

  for (sp in species_list) {
    sp_raw <- raw_data %>% filter(species == sp)
    n_records <- nrow(sp_raw)

    # Skip if < MIN_RECORDS
    if (n_records < MIN_RECORDS) {
      log_warn(LOG_FILE_PATH, paste("Skipping", sp, "- insufficient records:", n_records, "<", MIN_RECORDS))
      skipped_species[[sp]] <- n_records
      next
    }

    sp_points <- points_data %>% filter(species == sp)

    # Perform replicates
    replicate_shifts <- numeric(N_REPLICATES)

    for (i in 1:N_REPLICATES) {
      # Subsample 50% of records
      sample_indices <- sample(1:nrow(sp_points), size = floor(nrow(sp_points) * SUBSAMPLE_RATIO))
      sp_sample <- sp_points[sample_indices, ]

      # Compute shift
      shift_val <- compute_niche_shift(sp_sample)
      replicate_shifts[i] <- shift_val
    }

    # Calculate statistics
    mean_shift <- mean(replicate_shifts, na.rm = TRUE)
    sd_shift <- sd(replicate_shifts, na.rm = TRUE)

    # Flag high variability
    is_flagged <- FALSE
    if (!is.na(sd_shift) && sd_shift >= SD_THRESHOLD) {
      is_flagged <- TRUE
      log_warn(LOG_FILE_PATH, paste("Flagged", sp, "- high variability (SD =", round(sd_shift, 4), ">= ", SD_THRESHOLD, ")"))
      flagged_species[[sp]] <- sd_shift
    }

    # Store result
    results_list[[sp]] <- data.frame(
      species = sp,
      n_original_records = n_records,
      n_subsampled_records = floor(n_records * SUBSAMPLE_RATIO),
      mean_shift = mean_shift,
      sd_shift = sd_shift,
      is_flagged = is_flagged,
      stringsAsFactors = FALSE
    )
  }

  # Combine results
  if (length(results_list) > 0) {
    final_df <- bind_rows(results_list)
  } else {
    final_df <- data.frame(
      species = character(),
      n_original_records = integer(),
      n_subsampled_records = integer(),
      mean_shift = numeric(),
      sd_shift = numeric(),
      is_flagged = logical(),
      stringsAsFactors = FALSE
    )
  }

  # Ensure output directory exists
  if (!dir.exists(here("results"))) {
    dir.create(here("results"), recursive = TRUE)
  }

  # Write output
  write_csv(final_df, OUTPUT_SUMMARY_PATH)
  log_info(LOG_FILE_PATH, paste("Wrote sensitivity summary to", OUTPUT_SUMMARY_PATH))
  log_info(LOG_FILE_PATH, paste("Total species processed:", nrow(final_df)))
  log_info(LOG_FILE_PATH, paste("Species skipped (<", MIN_RECORDS, "records):", length(skipped_species)))
  log_info(LOG_FILE_PATH, paste("Species flagged (SD >= ", SD_THRESHOLD, "):", sum(final_df$is_flagged)))

  # Log detailed outcomes for FR-010
  log_info(LOG_FILE_PATH, "Subsampling outcomes summary:")
  for (sp in names(skipped_species)) {
    log_info(LOG_FILE_PATH, paste("  Skipped:", sp, "with", skipped_species[[sp]], "records"))
  }
  for (sp in names(flagged_species)) {
    log_info(LOG_FILE_PATH, paste("  Flagged:", sp, "with SD =", round(flagged_species[[sp]], 4)))
  }

  log_info(LOG_FILE_PATH, "Sensitivity analysis completed successfully")
}

# Run main
tryCatch({
  main()
}, error = function(e) {
  log_error(LOG_FILE_PATH, paste("Error during sensitivity analysis:", e$message))
  stop(e)
})
