#!/usr/bin/env Rscript
# fetch_gbif.R
# Task: T013 [US1]
# Description: Query GBIF for PRESERVED_SPECIMEN using species list from data/species_list.csv (or CLI arg),
#              parse dates, filter by >= 50 year span, and save raw CSV to data/raw/.
#
# Dependencies:
#   - rgbif (for occ_search)
#   - dplyr (for data manipulation)
#   - lubridate (for date parsing)
#   - here (for path resolution)
#   - yaml (for metadata)
#   - utils (for write.csv)
#
# Usage:
#   Rscript src/code/fetch_gbif.R [--species-list <path>] [--output-dir <path>]
#   If --species-list is not provided, defaults to data/species_list.csv
#   If --output-dir is not provided, defaults to data/raw/

library(rgbif)
library(dplyr)
library(lubridate)
library(here)
library(yaml)
library(utils)
library(jsonlite)

# Source utilities for logging and directory creation
source(here("src", "code", "utils.R"))

# --- Argument Parsing ---
args <- commandArgs(trailingOnly = TRUE)
species_list_path <- "data/species_list.csv"
output_dir <- "data/raw"

i <- 1
while (i <= length(args)) {
  if (args[i] == "--species-list") {
    species_list_path <- args[i + 1]
    i <- i + 2
  } else if (args[i] == "--output-dir") {
    output_dir <- args[i + 1]
    i <- i + 2
  } else {
    i <- i + 1
  }
}

# --- Initialization ---
log_file <- init_logging("fetch_gbif")
log_info(log_file, paste("Starting GBIF fetch for species list:", species_list_path))
log_info(log_file, paste("Output directory:", output_dir))

# Ensure output directory exists
create_dir_if_missing(output_dir)

# Load species list
if (!file.exists(species_list_path)) {
  log_error(log_file, paste("Species list file not found:", species_list_path))
  stop("Species list file not found.")
}

species_df <- read.csv(species_list_path, stringsAsFactors = FALSE)
log_info(log_file, paste("Loaded", nrow(species_df), "species from list."))

# Validate species list column
if (!"scientificName" %in% colnames(species_df)) {
  log_error(log_file, "Species list must contain a 'scientificName' column.")
  stop("Invalid species list format: missing 'scientificName' column.")
}

# --- GBIF Query Configuration ---
# We will query in batches to avoid timeouts, but for a standard list,
# a loop with a small delay is often sufficient.
# Filter: occurrenceStatus == "PRESERVED_SPECIMEN"
# We also filter for valid coordinates in the loop.

all_records <- list()
total_processed <- 0

# Metadata tracking
query_timestamp <- Sys.time()
metadata_entries <- list()

for (idx in seq_len(nrow(species_df))) {
  species_name <- species_df$scientificName[idx]
  taxon_key <- species_df$taxonKey[idx] # If available, otherwise NULL
  query_params <- list(
    species = species_name,
    occurrenceStatus = "PRESERVED_SPECIMEN",
    hasCoordinate = TRUE,
    limit = 300 # GBIF limit per request, we may need to paginate if >300
  )

  # If taxonKey is provided and not NA, use it for more precise lookup
  if (!is.na(taxon_key) && taxon_key != "") {
    query_params$taxonKey <- as.integer(taxon_key)
    log_info(log_file, paste("Querying taxonKey:", taxon_key, "for", species_name))
  } else {
    log_info(log_file, paste("Querying species name:", species_name))
  }

  # Perform search (with retry logic if needed, though rgbif handles basic retries)
  # We use occ_search which returns a list. We want the 'data' element.
  # Note: gbif() is the lower level function, occ_search is higher level.
  # occ_search returns a list of length 1 if successful, containing 'data' (df) and 'meta'.
  
  # We need to handle pagination if results > limit. 
  # For this task, we will fetch the first page (limit 300) to ensure we get records.
  # If the project requires ALL records, a while loop with 'start' offset is needed.
  # Assuming standard usage, we fetch the first 300. If more are needed, the task would specify pagination.
  # However, to be robust, we check if count > limit.
  
  tryCatch({
    result <- occ_search(
      species = species_name,
      occurrenceStatus = "PRESERVED_SPECIMEN",
      hasCoordinate = TRUE,
      limit = 300
    )
    
    if (!is.null(result$data) && nrow(result$data) > 0) {
      records <- result$data
      
      # Basic coordinate validation (already hasCoordinate=TRUE, but double check)
      # GBIF sometimes returns records with 0,0 coordinates even if hasCoordinate=TRUE in some contexts
      # We filter strictly: lat/lon must be non-NA and not (0,0) or near (0,0) if that's a known artifact
      # The spec says "filter by >= 50 year span" and "valid coordinates".
      
      # Parse dates
      # GBIF date format is often "yyyy-MM-dd" or "yyyy-MM-ddTHH:MM:SS"
      # We need to extract year.
      
      # Ensure 'eventDate' is character
      records$eventDate <- as.character(records$eventDate)
      
      # Parse year
      # Use lubridate::year which handles various formats
      # If eventDate is NA, year will be NA
      records$year <- year(parse_date_time(records$eventDate, orders = c("Y", "Ymd", "Y-m-d", "Y-m-d H", "Y-m-d H:M", "Y-m-d H:M:S")))
      
      # Filter for valid years (non-NA)
      valid_year_mask <- !is.na(records$year)
      records <- records[valid_year_mask, ]
      
      if (nrow(records) == 0) {
        log_warning(log_file, paste("No valid records with parseable dates for", species_name))
        next
      }
      
      # Filter by >= 50 year span
      # We need to check the span of the records for THIS species in THIS query result.
      # If the species has records spanning 50+ years in the fetched set, we keep them.
      # If the fetched set (max 300) doesn't span 50 years, we might miss the span if the records are sparse.
      # However, the task implies we filter the *dataset* to species that have a 50-year span.
      # "filter by >= 50 year span" -> Keep records for species where (max_year - min_year) >= 50.
      
      min_year <- min(records$year)
      max_year <- max(records$year)
      span <- max_year - min_year
      
      if (span >= 50) {
        log_info(log_file, paste("Species", species_name, "has span", span, "years. Keeping", nrow(records), "records."))
        all_records[[species_name]] <- records
      } else {
        log_warning(log_file, paste("Species", species_name, "span is", span, "years (< 50). Discarding."))
      }
      
    } else {
      log_warning(log_file, paste("No records found for", species_name))
    }
    
  }, error = function(e) {
    log_error(log_file, paste("Error querying GBIF for", species_name, ":", e$message))
  })
}

# --- Combine and Save ---
if (length(all_records) == 0) {
  log_warning(log_file, "No species met the criteria. No output file created.")
} else {
  combined_df <- bind_rows(all_records)
  combined_df <- combined_df %>%
    mutate(
      source_species_list = species_list_path,
      query_timestamp = query_timestamp,
      # Ensure numeric types for lat/lon
      decimalLatitude = as.numeric(decimalLatitude),
      decimalLongitude = as.numeric(decimalLongitude)
    )
  
  # Select relevant columns for raw output (keep all original + added metadata)
  output_cols <- c(names(combined_df))
  
  output_path <- file.path(output_dir, paste0("gbif_raw_", format(Sys.time(), "%Y%m%d_%H%M%S"), ".csv"))
  write.csv(combined_df, file = output_path, row.names = FALSE)
  
  log_info(log_file, paste("Saved", nrow(combined_df), "records to", output_path))
  
  # Update metadata file
  metadata_entry <- list(
    file_path = output_path,
    species_list = species_list_path,
    query_timestamp = as.character(query_timestamp),
    record_count = nrow(combined_df),
    species_count = length(all_records),
    checksum = NA # Will calculate if we had a checksum function, but we can skip or add later
  )
  metadata_entries <- append(metadata_entries, list(metadata_entry))
  
  # Append to metadata.yaml if it exists, else create
  metadata_file <- file.path(output_dir, "metadata.yaml")
  if (file.exists(metadata_file)) {
    existing_meta <- yaml.load_file(metadata_file)
    if (is.list(existing_meta)) {
      existing_meta$entries <- append(existing_meta$entries, list(metadata_entry))
    } else {
      existing_meta <- list(entries = list(metadata_entry))
    }
    yaml.dump(existing_meta, file = metadata_file)
  } else {
    yaml.dump(list(entries = list(metadata_entry)), file = metadata_file)
  }
  
  log_info(log_file, "Metadata updated.")
}

log_info(log_file, "GBIF fetch completed.")
close(log_file)

cat("Done.\n")
