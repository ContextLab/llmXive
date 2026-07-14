#!/usr/bin/env Rscript
# fetch_gbif.R
# Purpose: Query GBIF for PRESERVED_SPECIMEN records, parse dates, filter by >=50 year span,
#          and save raw CSV to data/raw/
# Dependencies: rgbif, dplyr, lubridate, here, yaml (from project setup T002)

library(rgbif)
library(dplyr)
library(lubridate)
library(here)
library(yaml)

# Source utilities for logging and directory creation
source(here("src", "code", "utils.R"))

# --- Configuration ---
# Default species list file path
default_species_file <- here("data", "species_list.csv")

# Output path for raw data
output_dir <- here("data", "raw")
output_file <- file.path(output_dir, "gbif_raw_records.csv")

# Minimum year span required (50 years)
min_year_span <- 50

# --- Argument Parsing ---
args <- commandArgs(trailingOnly = TRUE)
species_file <- if (length(args) >= 1) args[1] else default_species_file

# Check if species file exists
if (!file.exists(species_file)) {
  log_error(paste("Species list file not found:", species_file))
  stop("Species list file not found. Please provide a valid path.")
}

# --- Main Execution ---
log_info("Starting GBIF data fetch for PRESERVED_SPECIMEN records...")

# Create output directory if it doesn't exist
ensure_directory(output_dir)

# Load species list
log_info(paste("Loading species list from:", species_file))
species_df <- read.csv(species_file, stringsAsFactors = FALSE)

# Validate species list columns
if (!"scientificName" %in% names(species_df)) {
  # Try to auto-detect if the column is named 'species' or similar
  if ("species" %in% names(species_df)) {
    names(species_df)[names(species_df) == "species"] <- "scientificName"
  } else {
    stop("Species list must contain a 'scientificName' column.")
  }
}

all_records <- data.frame()
total_species <- nrow(species_df)
processed_species <- 0

log_info(paste("Processing", total_species, "species..."))

for (i in seq_len(total_species)) {
  species_name <- species_df$scientificName[i]
  processed_species <- processed_species + 1
  
  log_info(paste("[", processed_species, "/", total_species, "] Fetching records for:", species_name))
  
  tryCatch({
    # Query GBIF for PRESERVED_SPECIMEN
    # Using occ_search with limit=10000 to avoid pagination complexity for initial fetch
    # In production, a more robust pagination handler might be needed
    result <- occ_search(
      scientificName = species_name,
      occurrenceStatus = "PRESERVED_SPECIMEN",
      limit = 10000
    )
    
    if (length(result$data) > 0) {
      df <- result$data
      
      # Basic filtering: remove records with missing coordinates
      df <- df %>%
        filter(!is.na(decimalLatitude) & !is.na(decimalLongitude)) %>%
        filter(decimalLatitude >= -90 & decimalLatitude <= 90) %>%
        filter(decimalLongitude >= -180 & decimalLongitude <= 180)
      
      if (nrow(df) > 0) {
        # Parse dates
        # GBIF provides 'eventDate' which can be a range or single date
        # We attempt to extract the start year for filtering
        df <- df %>%
          mutate(
            eventDateParsed = as.character(eventDate),
            year = case_when(
              # Handle ISO 8601 ranges like "1950/1960" or "1950-01/1960-01"
              grepl("/", eventDateParsed) ~ as.integer(strsplit(eventDateParsed, "/")[[1]][1]),
              # Handle simple year "1950"
              nchar(eventDateParsed) == 4 & grepl("^[0-9]{4}$", eventDateParsed) ~ as.integer(eventDateParsed),
              # Handle ranges with dash "1950-1960" (less common in GBIF but possible)
              grepl("-", eventDateParsed) ~ as.integer(strsplit(eventDateParsed, "-")[[1]][1]),
              TRUE ~ NA_integer_
            )
          )
        
        # Filter out records where year could not be parsed
        df <- df %>% filter(!is.na(year))
        
        # Calculate year span for the species based on available records
        # We need to check if the *available* records span >= 50 years
        if (nrow(df) > 0) {
          year_range <- max(df$year, na.rm = TRUE) - min(df$year, na.rm = TRUE)
          
          if (year_range >= min_year_span) {
            log_info(paste("  -> Keeping", nrow(df), "records for", species_name, 
                           "(Year span:", year_range, "years)"))
            all_records <- rbind(all_records, df)
          } else {
            log_warning(paste("  -> Skipping", species_name, 
                              "(Year span:", year_range, "years < ", min_year_span, ")"))
          }
        } else {
          log_warning(paste("  -> No valid records with parseable dates for", species_name))
        }
      } else {
        log_info(paste("  -> No valid coordinate records for", species_name))
      }
    } else {
      log_info(paste("  -> No records found for", species_name))
    }
    
  }, error = function(e) {
    log_error(paste("Error fetching data for", species_name, ":", e$message))
  })
}

if (nrow(all_records) > 0) {
  # Save raw records to CSV
  log_info(paste("Saving", nrow(all_records), "records to", output_file))
  write.csv(all_records, output_file, row.names = FALSE)
  
  # Update metadata
  log_info("Updating metadata.yaml...")
  metadata_file <- here("data", "metadata.yaml")
  current_metadata <- list()
  if (file.exists(metadata_file)) {
    current_metadata <- yaml.load_file(metadata_file)
  }
  
  # Append new fetch info
  fetch_info <- list(
    timestamp = Sys.time(),
    species_file = species_file,
    total_species_processed = total_species,
    records_saved = nrow(all_records),
    output_file = output_file,
    checksum = tools::md5sum(output_file)
  )
  
  # Store in a list to allow multiple fetches if needed, or overwrite
  current_metadata$last_gbif_fetch <- fetch_info
  
  yaml.write_file(current_metadata, metadata_file)
  
  log_info("Fetch complete. Output saved.")
} else {
  log_warning("No records met the criteria. No output file created.")
}

log_info("Script finished.")
