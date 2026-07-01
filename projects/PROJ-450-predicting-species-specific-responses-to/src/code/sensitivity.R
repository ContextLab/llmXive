# src/code/sensitivity.R
# Sensitivity Analysis for Niche Shifts (User Story 3)
# Implements subsampling of occurrence records to assess stability of niche shift estimates.
#
# T031: Perform random subsamples (50% of records, 10 replicates, set.seed(42))
# T032: Recompute niche shift magnitude for each replicate
# T033: Flag species with SD >= 0.2 and skip species with < 80 records
# T034: Output results to results/sensitivity_summary.csv

library(dplyr)
library(tidyr)
library(readr)
library(utils)

# Source utilities if available
utils_path <- file.path("src", "code", "utils.R")
if (file.exists(utils_path)) {
  source(utils_path)
} else {
  # Fallback logging if utils.R not yet loaded (though T004 should be done)
  log_info <- function(msg) message(paste("[INFO]", Sys.time(), "-", msg))
  log_warn <- function(msg) message(paste("[WARN]", Sys.time(), "-", msg))
}

#' Subsample records for a single species
#'
#' @param data A data frame containing occurrence records for one species.
#' @param fraction The fraction of records to keep (default 0.5).
#' @param seed The random seed for reproducibility.
#' @return A data frame with the subsampled records.
subsample_records <- function(data, fraction = 0.5, seed = NULL) {
  if (!is.null(seed)) {
    set.seed(seed)
  }

  n <- nrow(data)
  if (n < 2) {
    stop("Input data must have at least 2 records to subsample.")
  }

  # Calculate number of records to keep
  n_keep <- max(1, floor(n * fraction))

  # Randomly select indices
  indices <- sample(seq_len(n), size = n_keep, replace = FALSE)

  return(data[indices, ])
}

#' Compute niche shift magnitude (Euclidean distance in climate space)
#'
#' Assumes data has columns 'temp' and 'precip' and 'period' (e.g., "1970-2000", "1991-2020").
#' Calculates centroids per period and returns the Euclidean distance.
#'
#' @param data Data frame with climate variables and period column.
#' @return Numeric value of Euclidean distance.
compute_shift_magnitude <- function(data) {
  if (!all(c("temp", "precip", "period") %in% names(data))) {
    stop("Data must contain 'temp', 'precip', and 'period' columns.")
  }

  centroids <- data %>%
    group_by(period) %>%
    summarise(
      temp_mean = mean(temp, na.rm = TRUE),
      precip_mean = mean(precip, na.rm = TRUE),
      .groups = "drop"
    )

  if (nrow(centroids) < 2) {
    return(NA_real_)
  }

  # Assuming periods are ordered or we know which is which.
  # For simplicity, we assume the first row is period 1 and second is period 2.
  # In a real scenario, we might sort by period name if they are numeric ranges.
  p1 <- centroids[1, ]
  p2 <- centroids[2, ]

  dist <- sqrt(
    (p1$temp_mean - p2$temp_mean)^2 +
    (p1$precip_mean - p2$precip_mean)^2
  )

  return(dist)
}

#' Run sensitivity analysis for all species
#'
#' @param input_path Path to the input CSV with occurrence data (e.g., points_with_climate.csv).
#' @param output_path Path to save the sensitivity summary CSV.
#' @param n_replicates Number of subsampling replicates (default 10).
#' @param fraction Fraction of records to subsample (default 0.5).
#' @param min_records Minimum number of records required to run analysis (default 80).
#' @param seed Random seed for reproducibility (default 42).
run_sensitivity_analysis <- function(
  input_path = "data/processed/points_with_climate.csv",
  output_path = "results/sensitivity_summary.csv",
  n_replicates = 10,
  fraction = 0.5,
  min_records = 80,
  seed = 42
) {
  log_info("Starting sensitivity analysis.")

  # Check input file
  if (!file.exists(input_path)) {
    stop(paste("Input file not found:", input_path))
  }

  data <- read_csv(input_path)

  # Ensure required columns exist
  required_cols <- c("species", "temp", "precip", "period", "year")
  if (!all(required_cols %in% names(data))) {
    stop(paste("Input file missing required columns:", paste(setdiff(required_cols, names(data)), collapse = ", ")))
  }

  # Prepare output list
  results <- list()

  # Iterate over species
  species_list <- unique(data$species)
  log_info(paste("Processing", length(species_list), "species."))

  for (sp in species_list) {
    sp_data <- data %>% filter(species == sp)
    n_records <- nrow(sp_data)

    if (n_records < min_records) {
      log_warn(paste("Skipping species", sp, "with only", n_records, "records (<", min_records, ")."))
      results[[sp]] <- list(
        species = sp,
        n_records = n_records,
        mean_shift = NA_real_,
        sd_shift = NA_real_,
        flagged = FALSE,
        status = "Skipped (insufficient records)"
      )
      next
    }

    shifts <- numeric(n_replicates)

    for (i in 1:n_replicates) {
      # Subsample
      subsample <- subsample_records(sp_data, fraction = fraction, seed = seed + i)

      # Compute shift
      shift_val <- compute_shift_magnitude(subsample)

      if (is.na(shift_val)) {
        log_warn(paste("Could not compute shift for species", sp, "in replicate", i))
      }
      shifts[i] <- shift_val
    }

    mean_shift <- mean(shifts, na.rm = TRUE)
    sd_shift <- sd(shifts, na.rm = TRUE)

    # Flag if SD >= 0.2
    is_flagged <- ifelse(!is.na(sd_shift) && sd_shift >= 0.2, TRUE, FALSE)

    results[[sp]] <- list(
      species = sp,
      n_records = n_records,
      mean_shift = mean_shift,
      sd_shift = sd_shift,
      flagged = is_flagged,
      status = "Completed"
    )
  }

  # Convert to data frame
  output_df <- bind_rows(lapply(results, as.data.frame))

  # Ensure column types
  output_df <- output_df %>%
    mutate(
      flagged = as.logical(flagged),
      status = as.character(status)
    )

  # Save output
  dir.create(dirname(output_path), showWarnings = FALSE, recursive = TRUE)
  write_csv(output_df, output_path)

  log_info(paste("Sensitivity analysis complete. Results saved to", output_path))

  # Log summary
  flagged_count <- sum(output_df$flagged, na.rm = TRUE)
  log_info(paste("Total species processed:", nrow(output_df)))
  log_info(paste("Species flagged for high variability (SD >= 0.2):", flagged_count))

  return(output_df)
}

# Execute if run as script
if (!interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  input_file <- if (length(args) >= 1) args[1] else "data/processed/points_with_climate.csv"
  output_file <- if (length(args) >= 2) args[2] else "results/sensitivity_summary.csv"

  run_sensitivity_analysis(input_path = input_file, output_path = output_file)
}