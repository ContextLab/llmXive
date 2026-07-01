#!/usr/bin/env Rscript
# Task T036a: Validate SC-001
# Requirement: Check logs to confirm >= 90% of supplied species with >= 50 valid records
# produced a complete centroids.csv record for both periods (1970-2000 and 1991-2020).

library(dplyr)
library(readr)
library(stringr)
library(lubridate)
library(here)

# Configuration
LOG_FILE <- here("data", "logs", "pipeline.log")
CENTROIDS_FILE <- here("data", "processed", "centroids.csv")
RAW_DATA_FILE <- here("data", "raw", "occurrence_data.csv") # Assumed source of raw species list
THRESHOLD <- 0.90

# Helper: Parse log to find species with >= 50 records
parse_species_counts <- function(log_path) {
  if (!file.exists(log_path)) {
    stop(paste("Log file not found:", log_path))
  }

  lines <- readLines(log_path)

  # Pattern to capture: "Species: [Name], Records: [Count]" or similar log format from T013/T017
  # We look for lines indicating record counts per species, likely from fetch_gbif.R or compute_centroids.R
  # Assuming a format like: "INFO [timestamp] Processed species 'SpeciesName': 150 records found."
  # or "INFO [timestamp] Filtered species 'SpeciesName': 60 records remain."

  # Regex to extract species name and count
  # Adjust based on actual log format from T017. Using a robust pattern:
  # Look for "species" (case insensitive) followed by name and "records" with a number.
  pattern <- "species.*['\"]?([A-Za-z0-9_. ]+)['\"]?.*records.*[:\\s]*(\\d+)"

  matches <- str_match(lines, pattern)
  if (is.na(matches[1, 1])) {
    # Fallback: Try a stricter log format if the generic one fails
    # Example: "INFO 2023-01-01 ... Species: Genus_species, Count: 50"
    pattern2 <- "Species:\\s*([A-Za-z0-9_.]+).*Count:\\s*(\\d+)"
    matches <- str_match(lines, pattern2)
  }

  if (all(is.na(matches[, 1]))) {
    warning("Could not parse species counts from log. Check log format.")
    return(data.frame(species = character(), count = integer()))
  }

  df <- data.frame(
    species = trimws(matches[, 2]),
    count = as.integer(matches[, 3]),
    stringsAsFactors = FALSE
  )

  # Filter for species with >= 50 records
  valid_species <- df %>%
    filter(count >= 50) %>%
    distinct(species, .keep_all = TRUE)

  return(valid_species)
}

# Helper: Check centroids.csv for completeness
check_centroids_completeness <- function(centroids_path, species_list) {
  if (!file.exists(centroids_path)) {
    stop(paste("Centroids file not found:", centroids_path))
  }

  df <- read_csv(centroids_path, show_col_types = FALSE)

  # Expected columns: species, period, temp_mean, precip_mean (or similar)
  # We need to verify that for each species in species_list, there are exactly 2 rows (one per period)
  # Periods are likely "1970-2000" and "1991-2020"

  required_periods <- c("1970-2000", "1991-2020")

  # Normalize species names in centroids if necessary (e.g., remove quotes)
  df$species <- gsub("['\"]", "", df$species)

  results <- lapply(species_list$species, function(sp) {
    sp_data <- df %>% filter(species == sp)
    periods_found <- unique(sp_data$period) # Assuming 'period' column exists
    # If 'period' column doesn't exist, we might infer from other columns or row count
    # Assuming standard output from compute_centroids.R has a 'period' column

    # Check if both required periods are present
    has_both <- all(required_periods %in% periods_found)
    count <- nrow(sp_data)

    list(
      species = sp,
      has_complete = has_both,
      count = count
    )
  })

  return(do.call(rbind, lapply(results, as.data.frame)))
}

main <- function() {
  cat("Starting SC-001 Validation...\n")

  # 1. Identify species with >= 50 valid records from logs
  cat("Parsing logs for species with >= 50 records...\n")
  species_with_enough_data <- parse_species_counts(LOG_FILE)

  if (nrow(species_with_enough_data) == 0) {
    cat("ERROR: No species with >= 50 records found in logs. Cannot validate SC-001.\n")
    quit(status = 1)
  }

  cat(sprintf("Found %d species with >= 50 records.\n", nrow(species_with_enough_data)))

  # 2. Check centroids.csv for these species
  cat("Checking centroids.csv for completeness...\n")
  completeness_results <- check_centroids_completeness(CENTROIDS_FILE, species_with_enough_data)

  # 3. Calculate success rate
  total_candidates <- nrow(completeness_results)
  successful <- sum(completeness_results$has_complete)
  success_rate <- successful / total_candidates

  cat(sprintf("Total species candidates: %d\n", total_candidates))
  cat(sprintf("Species with complete records (both periods): %d\n", successful))
  cat(sprintf("Success Rate: %.2f%% (Threshold: %.2f%%)\n", success_rate * 100, THRESHOLD * 100))

  if (success_rate >= THRESHOLD) {
    cat("RESULT: PASS - SC-001 validated successfully.\n")
    quit(status = 0)
  } else {
    cat("RESULT: FAIL - SC-001 validation failed.\n")
    # List failing species for debugging
    failing <- completeness_results %>% filter(!has_complete)
    cat("Failing species:\n")
    print(failing$species)
    quit(status = 1)
  }
}

main()
