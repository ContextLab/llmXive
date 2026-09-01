#!/usr/bin/env Rscript
# sensitivity.R - User Story 3: Sensitivity Analysis of Sampling Effort
#
# Performs random subsampling of occurrence records (50%, 10 replicates),
# recomputes niche shift magnitude (ΔN) for each replicate, and calculates
# mean/SD of shifts. Flags species with high variability (SD >= 0.2).
#
# Outputs:
#   - results/sensitivity_summary.csv: Summary statistics per species
#   - logs/sensitivity.log: Detailed log of subsampling outcomes (FR-010)
#
# Dependencies:
#   - data/raw/<species>_raw.csv (or similar pattern from T013)
#   - data/processed/centroids.csv (for baseline shift reference if needed, though we recompute)
#   - src/code/utils.R (logging, directory creation)
#   - src/code/compute_shifts.R (for re-computing ΔN on subsamples)

# Load dependencies
library(dplyr)
library(tidyr)
library(readr)
library(lubridate)
library(here)

# Source project utilities
source(here("src", "code", "utils.R"))

# Configuration
set.seed(42)
SUBSAMPLE_FRACTION <- 0.5
NUM_REPLICATES <- 10
MIN_RECORDS_THRESHOLD <- 80
HIGH_VARIABILITY_THRESHOLD <- 0.2
RESULTS_DIR <- here("results")
LOGS_DIR <- here("logs")
RAW_DATA_DIR <- here("data", "raw")
PROCESSED_DATA_DIR <- here("data", "processed")

# Ensure output directories exist
create_directory(RESULTS_DIR)
create_directory(LOGS_DIR)

# Initialize logging
log_file <- file.path(LOGS_DIR, "sensitivity.log")
init_logging(log_file, task_name = "Sensitivity Analysis (US3)")

log_message("Starting sensitivity analysis for sampling effort.")
log_message(paste0("Configuration: Subsample fraction = ", SUBSAMPLE_FRACTION,
                   ", Replicates = ", NUM_REPLICATES,
                   ", Min records = ", MIN_RECORDS_THRESHOLD))

# Load raw occurrence data
# Expecting files like: data/raw/<species_name>_raw.csv
# We will look for all CSVs in data/raw that match the pattern of species data
# Alternatively, if there is a master list, use that. For now, we scan the directory.
raw_files <- list.files(RAW_DATA_DIR, pattern = "_raw\\.csv$", full.names = TRUE)

if (length(raw_files) == 0) {
  log_message("ERROR: No raw occurrence data files found in data/raw/. Exiting.", level = "ERROR")
  stop("No raw occurrence data files found. Ensure T013 has run successfully.")
}

log_message(paste0("Found ", length(raw_files), " raw occurrence files."))

# Function to compute niche shift (ΔN) for a given dataset
# This mimics the logic in compute_shifts.R but simplified for local use
# It expects a dataframe with columns: species, period, temp, precip (standardized)
compute_delta_n <- function(df_species) {
  # df_species should have rows for two periods (e.g., "1970-2000", "1991-2020")
  # We assume global z-scoring was already applied to the columns 'temp' and 'precip'
  # If not, we would need to pass the global means/SDs, but for this task,
  # we assume the input data is already standardized as per T021 logic.

  # Check if we have exactly 2 periods
  periods <- unique(df_species$period)
  if (length(periods) != 2) {
    return(NA) # Cannot compute shift with != 2 periods
  }

  # Calculate centroids for each period
  centroid_p1 <- df_species %>%
    filter(period == periods[1]) %>%
    summarise(temp_mean = mean(temp, na.rm = TRUE),
              precip_mean = mean(precip, na.rm = TRUE))

  centroid_p2 <- df_species %>%
    filter(period == periods[2]) %>%
    summarise(temp_mean = mean(temp, na.rm = TRUE),
              precip_mean = mean(precip, na.rm = TRUE))

  # Euclidean distance in climate space
  delta_n <- sqrt(
    (centroid_p2$temp_mean - centroid_p1$temp_mean)^2 +
    (centroid_p2$precip_mean - centroid_p1$precip_mean)^2
  )

  return(delta_n)
}

# Prepare results dataframe
results_list <- list()

for (file_path in raw_files) {
  species_name <- tools::file_path_sans_ext(basename(file_path))
  species_name <- gsub("_raw$", "", species_name)

  log_message(paste0("Processing species: ", species_name))

  tryCatch({
    # Read raw data
    raw_data <- read_csv(file_path, show_col_types = FALSE)

    # Validate necessary columns
    required_cols <- c("species", "decimalLatitude", "decimalLongitude", "eventDate", "temp", "precip", "period")
    if (!all(required_cols %in% names(raw_data))) {
      log_message(paste0("Skipping ", species_name, ": Missing required columns in raw data."), level = "WARN")
      next
    }

    # Filter for valid records (non-NA climate, valid coordinates)
    valid_data <- raw_data %>%
      filter(!is.na(temp), !is.na(precip),
             !is.na(decimalLatitude), !is.na(decimalLongitude))

    record_count <- nrow(valid_data)
    log_message(paste0("  Valid records for ", species_name, ": ", record_count))

    # Check minimum record threshold
    if (record_count < MIN_RECORDS_THRESHOLD) {
      log_message(paste0("  Skipping ", species_name, ": Record count (", record_count,
                         ") is below threshold (", MIN_RECORDS_THRESHOLD, ")."), level = "WARN")
      next
    }

    # Perform subsampling replicates
    replicate_shifts <- numeric(NUM_REPLICATES)

    for (i in 1:NUM_REPLICATES) {
      # Random subsample
      sample_indices <- sample(seq_len(nrow(valid_data)),
                               size = floor(nrow(valid_data) * SUBSAMPLE_FRACTION))
      subsample_data <- valid_data[sample_indices, ]

      # Compute shift for this replicate
      shift_val <- compute_delta_n(subsample_data)

      if (is.na(shift_val)) {
        log_message(paste0("    Replicate ", i, ": Could not compute shift (missing period data)."), level = "WARN")
        replicate_shifts[i] <- NA
      } else {
        replicate_shifts[i] <- shift_val
      }
    }

    # Calculate mean and SD, ignoring NAs
    mean_shift <- mean(replicate_shifts, na.rm = TRUE)
    sd_shift <- sd(replicate_shifts, na.rm = TRUE)

    # Flag high variability
    is_high_variability <- FALSE
    if (!is.na(sd_shift) && sd_shift >= HIGH_VARIABILITY_THRESHOLD) {
      is_high_variability <- TRUE
      log_message(paste0("  WARNING: ", species_name, " flagged for high variability (SD = ",
                         round(sd_shift, 4), " >= ", HIGH_VARIABILITY_THRESHOLD, ")."), level = "WARN")
    }

    # Store results
    results_list[[species_name]] <- data.frame(
      species = species_name,
      total_records = record_count,
      subsample_records_avg = mean(floor(nrow(valid_data) * SUBSAMPLE_FRACTION)),
      replicate_count = sum(!is.na(replicate_shifts)),
      mean_shift = mean_shift,
      sd_shift = sd_shift,
      high_variability = is_high_variability,
      stringsAsFactors = FALSE
    )

    log_message(paste0("  Completed ", species_name, ": Mean ΔN = ",
                       round(mean_shift, 4), ", SD = ", round(sd_shift, 4)))

  }, error = function(e) {
    log_message(paste0("ERROR processing ", species_name, ": ", conditionMessage(e)), level = "ERROR")
  })
}

# Combine results into a single dataframe
if (length(results_list) > 0) {
  sensitivity_summary <- bind_rows(results_list)

  # Write to CSV
  output_path <- file.path(RESULTS_DIR, "sensitivity_summary.csv")
  write_csv(sensitivity_summary, output_path)
  log_message(paste0("Sensitivity summary written to: ", output_path))

  # Append detailed log entries for subsampling outcomes (FR-010)
  # We already logged per-species details, but let's add a final summary block
  log_message("--- Sensitivity Analysis Summary ---")
  log_message(paste0("Total species processed: ", nrow(sensitivity_summary)))
  log_message(paste0("Species with high variability (SD >= ", HIGH_VARIABILITY_THRESHOLD, "): ",
                     sum(sensitivity_summary$high_variability)))
  log_message(paste0("Average mean shift across all species: ",
                     round(mean(sensitivity_summary$mean_shift, na.rm = TRUE), 4)))
  log_message(paste0("Average SD across all species: ",
                     round(mean(sensitivity_summary$sd_shift, na.rm = TRUE), 4)))
  log_message("Sensitivity analysis completed successfully.")

} else {
  log_message("No species met the criteria for sensitivity analysis. No output file generated.", level = "WARN")
  # Still create an empty file or a file with headers to indicate the run happened?
  # The task says "Output results/sensitivity_summary.csv". If empty, we should probably create it with headers.
  empty_df <- data.frame(
    species = character(),
    total_records = integer(),
    subsample_records_avg = numeric(),
    replicate_count = integer(),
    mean_shift = numeric(),
    sd_shift = numeric(),
    high_variability = logical(),
    stringsAsFactors = FALSE
  )
  output_path <- file.path(RESULTS_DIR, "sensitivity_summary.csv")
  write_csv(empty_df, output_path)
  log_message(paste0("Empty sensitivity summary written to: ", output_path))
}

log_message("Script execution finished.")
