#!/usr/bin/env Rscript
# fetch_gbif.R
# Implementation for T013: Query GBIF for PRESERVED_SPECIMEN, parse dates,
# filter by >=50 year span, and save raw CSV.

library(rgbif)
library(dplyr)
library(lubridate)
library(here)
library(yaml)

# Source utility functions
source(here("code", "utils.R"))

main <- function() {
  # 1. Load configuration
  config_path <- here("data", "metadata.yaml")
  if (file.exists(config_path)) {
    config <- yaml::read_yaml(config_path)
  } else {
    config <- list()
  }
  
  # 2. Determine species list
  # Priority: CLI arg > data/species_list.csv
  args <- commandArgs(trailingOnly = TRUE)
  species_arg <- if (length(args) > 0) args[1] else NULL
  
  if (!is.null(species_arg) && file.exists(species_arg)) {
    log_info("Loading species list from CLI arg: %s", species_arg)
    species_list <- read.csv(species_arg, stringsAsFactors = FALSE)
  } else {
    default_path <- here("data", "species_list.csv")
    if (file.exists(default_path)) {
      log_info("Loading species list from default: %s", default_path)
      species_list <- read.csv(default_path, stringsAsFactors = FALSE)
    } else {
      stop("No species list found. Provide a CSV path or place species_list.csv in data/")
    }
  }
  
  # Expect column 'scientificName' or 'species'
  if ("scientificName" %in% names(species_list)) {
    species_vec <- unique(species_list$scientificName)
  } else if ("species" %in% names(species_list)) {
    species_vec <- unique(species_list$species)
  } else {
    stop("Species list must contain column 'scientificName' or 'species'")
  }
  
  log_info("Found %d unique species to process", length(species_vec))
  
  # Ensure output directory exists
  out_dir <- here("data", "raw")
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  
  all_records <- list()
  processed_count <- 0
  failed_species <- c()
  
  # 3. Iterate over species
  for (sp in species_vec) {
    log_info("Processing species: %s", sp)
    
    tryCatch({
      # Query GBIF for PRESERVED_SPECIMEN
      # Using occ_search with limit=10000 per species to avoid timeout on single call
      # Note: For very large datasets, pagination would be needed, but this is a robust start.
      # We set occurrenceStatus explicitly.
      
      res <- occ_search(
        scientificName = sp,
        occurrenceStatus = "PRESERVED_SPECIMEN",
        limit = 10000,
        return = "data"
      )
      
      if (length(res$data) == 0) {
        log_warn("No records found for %s", sp)
        next
      }
      
      df <- res$data
      
      # Filter: Must have valid coordinates
      df <- df %>%
        filter(!is.na(decimalLatitude) & !is.na(decimalLongitude)) %>%
        filter(decimalLatitude >= -90 & decimalLatitude <= 90) %>%
        filter(decimalLongitude >= -180 & decimalLongitude <= 180)
      
      if (nrow(df) == 0) {
        log_warn("No valid coordinates for %s", sp)
        next
      }
      
      # Parse dates: Try multiple common formats
      # GBIF often provides 'eventDate' as ISO8601 or year-only
      df$year <- NA
      if ("eventDate" %in% names(df)) {
        # Extract year from eventDate string
        df$year <- as.integer(sub("-.*", "", as.character(df$eventDate)))
      } else if ("year" %in% names(df)) {
        df$year <- as.integer(df$year)
      }
      
      # Remove rows without a valid year
      df <- df %>% filter(!is.na(year) & year > 1900)
      
      if (nrow(df) == 0) {
        log_warn("No valid years for %s", sp)
        next
      }
      
      # Calculate span for this species
      min_year <- min(df$year)
      max_year <- max(df$year)
      span <- max_year - min_year
      
      if (span < 50) {
        log_warn("Species %s has span %d years (< 50). Skipping.", sp, span)
        next
      }
      
      # Keep records that contribute to the span (or all if they fall within the 50yr window logic)
      # Requirement: "filter by >= 50 year span". 
      # Interpretation: Keep the species only if the total range of years in its records is >= 50.
      # We keep all records for that species to compute centroids later.
      
      df$species_name <- sp
      df$source_query_year <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
      
      all_records[[sp]] <- df
      processed_count <- processed_count + 1
      log_info("Success for %s: %d records, span %d years", sp, nrow(df), span)
      
    }, error = function(e) {
      log_error("Failed to process %s: %s", sp, e$message)
      failed_species <- c(failed_species, sp)
    })
  }
  
  if (length(all_records) == 0) {
    stop("No species met the criteria (>=50 year span, valid data). Check species list and API.")
  }
  
  # Combine into one data frame
  final_df <- bind_rows(all_records)
  
  # Select and order columns for output
  output_cols <- c(
    "species_name", "decimalLatitude", "decimalLongitude", 
    "year", "eventDate", "scientificName", "gbifID", 
    "basisOfRecord", "source_query_year"
  )
  
  # Only keep columns that exist
  existing_cols <- output_cols[output_cols %in% names(final_df)]
  final_df <- final_df[, existing_cols]
  
  # 4. Save to CSV
  out_file <- here("data", "raw", "gbif_preserved_specimens.csv")
  write.csv(final_df, out_file, row.names = FALSE)
  
  log_info("Successfully saved %d records to %s", nrow(final_df), out_file)
  
  # Update metadata
  if (file.exists(config_path)) {
    config$last_query_time <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
    config$last_query_species_count <- length(species_vec)
    config$last_query_success_count <- processed_count
    config$files <- c(config$files, list(
      list(
        path = "data/raw/gbif_preserved_specimens.csv",
        checksum = digest::digest(final_df, algo = "md5", serialize = FALSE)
      )
    ))
    yaml::write_yaml(config, config_path)
  }
  
  return(invisible(TRUE))
}

if (!interactive()) {
  main()
}
