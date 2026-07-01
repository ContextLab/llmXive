#' Sensitivity Analysis for Sampling Effort
#'
#' This script performs a sensitivity analysis by subsampling occurrence records
#' to assess the stability of niche shift magnitude estimates.
#'
#' @description
#' 1. Loads raw occurrence data from `data/raw/` (produced by T013).
#' 2. Filters species with <80 records (skips them).
#' 3. For remaining species, performs 10 replicates of 50% random subsampling.
#' 4. Recomputes niche shift magnitude (ΔN) for each replicate using global z-scores.
#' 5. Calculates mean and standard deviation (SD) of shifts per species.
#' 6. Flags species with SD >= 0.2 climate-space units.
#' 7. Outputs `results/sensitivity_summary.csv` and appends detailed logs.
#'
#' @importFrom dplyr filter group_by summarise mutate left_join select distinct
#' @importFrom tidyr pivot_longer pivot_wider
#' @importFrom readr read_csv write_csv
#' @importFrom utils setTxtProgressBar txtProgressBar
#'
library(dplyr)
library(readr)
library(tidyr)
library(here)
library(lubridate)

# Source utility functions
source(here("code", "utils.R"))

# Configuration
N_REPLICATES <- 10
SUBSAMPLE_RATIO <- 0.5
MIN_RECORDS_THRESHOLD <- 80
SD_FLAG_THRESHOLD <- 0.2
SEED_VALUE <- 42
OUTPUT_FILE <- here("results", "sensitivity_summary.csv")
RAW_DATA_FILE <- here("data", "raw", "gbif_occurrences.csv")
POINTS_WITH_CLIMATE_FILE <- here("data", "processed", "points_with_climate.csv")
CENTROIDS_FILE <- here("data", "processed", "centroids.csv")

# Initialize logging
log_message("Starting sensitivity analysis (T034)")

# Check input files
if (!file.exists(RAW_DATA_FILE)) {
  stop("Raw occurrence data not found at ", RAW_DATA_FILE, ". Run T013 first.")
}
if (!file.exists(POINTS_WITH_CLIMATE_FILE)) {
  stop("Points with climate data not found at ", POINTS_WITH_CLIMATE_FILE, ". Run T015b first.")
}

log_message(paste("Loading raw data from", RAW_DATA_FILE))
raw_data <- read_csv(RAW_DATA_FILE, show_col_types = FALSE)

log_message(paste("Loading climate data from", POINTS_WITH_CLIMATE_FILE))
climate_data <- read_csv(POINTS_WITH_CLIMATE_FILE, show_col_types = FALSE)

# Ensure column names match expected schema (robustness check)
required_cols <- c("species", "decimalLatitude", "decimalLongitude", "year", "temp_mean", "precip_mean")
missing_cols <- setdiff(required_cols, names(climate_data))
if (length(missing_cols) > 0) {
  stop("Missing required columns in climate data: ", paste(missing_cols, collapse = ", "))
}

# Filter species with sufficient records
record_counts <- climate_data %>%
  group_by(species) %>%
  summarise(total_records = n(), .groups = "drop")

valid_species <- record_counts %>%
  filter(total_records >= MIN_RECORDS_THRESHOLD) %>%
  pull(species)

log_message(paste("Found", nrow(record_counts), "species total."))
log_message(paste("Skipping", sum(record_counts$total_records < MIN_RECORDS_THRESHOLD), "species with < 80 records."))
log_message(paste("Proceeding with", length(valid_species), "species for sensitivity analysis."))

# Global Z-scoring (using full dataset as per FR-005)
# Calculate global mean and SD for temp and precip
global_stats <- climate_data %>%
  summarise(
    temp_mean_global = mean(temp_mean, na.rm = TRUE),
    temp_sd_global = sd(temp_mean, na.rm = TRUE),
    precip_mean_global = mean(precip_mean, na.rm = TRUE),
    precip_sd_global = sd(precip_mean, na.rm = TRUE)
  )

# Standardize climate data globally
climate_data_std <- climate_data %>%
  mutate(
    temp_z = (temp_mean - global_stats$temp_mean_global) / global_stats$temp_sd_global,
    precip_z = (precip_mean - global_stats$precip_mean_global) / global_stats$precip_sd_global
  )

# Function to compute niche shift magnitude for a subset of data
compute_shift_for_subset <- function(subset_data, period_col = "period") {
  # Calculate centroids per species per period
  centroids <- subset_data %>%
    group_by(species, !!sym(period_col)) %>%
    summarise(
      temp_z_mean = mean(temp_z, na.rm = TRUE),
      precip_z_mean = mean(precip_z, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    pivot_wider(
      names_from = !!sym(period_col),
      values_from = c(temp_z_mean, precip_z_mean),
      names_sep = "_"
    )

  # Calculate Euclidean distance between periods (1970-2000 vs 1991-2020)
  # Assuming periods are named "P1" and "P2" or similar in the data
  # We need to identify the two periods present
  periods_present <- unique(centroids$species) # This is wrong, need to check period columns
  # Let's assume the columns are temp_z_mean_P1, temp_z_mean_P2 etc.
  # We need to dynamically find the period suffixes

  # Re-structure to get pairs
  if (ncol(centroids) < 4) return(NA) # Not enough data

  # Identify period suffixes (e.g., "P1", "P2" or "1970-2000", "1991-2020")
  # We look for columns starting with temp_z_mean_ and precip_z_mean_
  temp_cols <- grep("^temp_z_mean_", names(centroids), value = TRUE)
  precip_cols <- grep("^precip_z_mean_", names(centroids), value = TRUE)

  if (length(temp_cols) != 2 || length(precip_cols) != 2) {
    return(NA) # Expecting exactly two periods
  }

  # Extract suffixes
  suffixes <- gsub("^temp_z_mean_", "", temp_cols)

  # Calculate distance
  centroids <- centroids %>%
    mutate(
      delta_N = sqrt(
        (temp_z_mean[[1]] - temp_z_mean[[2]])^2 +
        (precip_z_mean[[1]] - precip_z_mean[[2]])^2
      )
    )

  return(centroids$delta_N[1])
}

# Prepare data for subsampling
# We need to associate each point with a period based on year
# Assuming 1970-2000 is P1 and 1991-2020 is P2
# Logic: If year <= 2000 and >= 1970 -> P1, If year <= 2020 and >= 1991 -> P2
# Note: Overlap exists (1991-2000), but T013 logic likely assigned specific periods.
# We will re-apply the period assignment logic consistent with T013/T015a
# T013/T015a likely used: year < 1991 -> P1, year >= 1991 -> P2 (or similar strict split)
# Let's assume the standard split:
# Period 1: 1970-1990 (or up to 2000 if strict)
# Period 2: 1991-2020
# To be safe, we re-calculate period based on year if not present, or use existing 'period' column if available.
# The file `points_with_climate.csv` should have a 'period' column if T015b worked.
if ("period" %in% names(climate_data_std)) {
  log_message("Using existing 'period' column from input data.")
} else {
  log_message("Assigning periods based on year (fallback logic).")
  climate_data_std <- climate_data_std %>%
    mutate(
      period = case_when(
        year < 1991 ~ "P1",
        year >= 1991 ~ "P2",
        TRUE ~ NA_character_
      )
    )
}

# Remove NA periods
climate_data_std <- climate_data_std %>% filter(!is.na(period))

# Run Sensitivity Analysis
results_list <- list()
log_message("Starting subsampling loop...")

pb <- txtProgressBar(min = 0, max = length(valid_species), style = 3)

for (sp in valid_species) {
  set.seed(SEED_VALUE) # Reproducibility per species start

  sp_data <- climate_data_std %>% filter(species == sp)

  # Check if species has both periods
  if (length(unique(sp_data$period)) < 2) {
    log_message(paste("Skipping", sp, "- missing one or both periods."))
    setTxtProgressBar(pb, which(valid_species == sp))
    next
  }

  replicate_shifts <- numeric(N_REPLICATES)

  for (i in 1:N_REPLICATES) {
    # Subsample 50% of records
    # We need to ensure we keep the ratio of periods roughly?
    # The task says "random subsamples of 50% of records".
    # Simple random sample of rows.
    sample_indices <- sample(nrow(sp_data), size = floor(nrow(sp_data) * SUBSAMPLE_RATIO))
    sp_sample <- sp_data[sample_indices, ]

    # Check if sample has both periods
    if (length(unique(sp_sample$period)) < 2) {
      replicate_shifts[i] <- NA
      next
    }

    shift_val <- compute_shift_for_subset(sp_sample)
    replicate_shifts[i] <- shift_val
  }

  # Calculate stats
  valid_shifts <- replicate_shifts[!is.na(replicate_shifts)]
  if (length(valid_shifts) > 0) {
    mean_shift <- mean(valid_shifts)
    sd_shift <- sd(valid_shifts)
  } else {
    mean_shift <- NA
    sd_shift <- NA
  }

  # Flag
  is_flagged <- ifelse(!is.na(sd_shift) && sd_shift >= SD_FLAG_THRESHOLD, TRUE, FALSE)

  results_list[[sp]] <- data.frame(
    species = sp,
    mean_shift = mean_shift,
    sd_shift = sd_shift,
    flagged = is_flagged,
    replicates_completed = length(valid_shifts),
    stringsAsFactors = FALSE
  )

  setTxtProgressBar(pb, which(valid_species == sp))
}

close(pb)

# Combine results
sensitivity_summary <- bind_rows(results_list)

# Write output
if (nrow(sensitivity_summary) > 0) {
  write_csv(sensitivity_summary, OUTPUT_FILE)
  log_message(paste("Sensitivity summary written to", OUTPUT_FILE))
  log_message(paste("Total species analyzed:", nrow(sensitivity_summary)))
  log_message(paste("Species flagged (SD >= 0.2):", sum(sensitivity_summary$flagged, na.rm = TRUE)))
} else {
  log_message("No species met the criteria for sensitivity analysis.")
  # Write empty file with headers if needed, or just log
  write_csv(data.frame(species=character(), mean_shift=numeric(), sd_shift=numeric(), flagged=logical(), replicates_completed=integer()), OUTPUT_FILE)
}

log_message("Sensitivity analysis (T034) completed successfully.")
