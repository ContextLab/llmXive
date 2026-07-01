# Fetch GBIF Occurrence Data
# Task: T006 (Skeleton) & T013 (Implementation)
# Queries GBIF for PRESERVED_SPECIMEN records, resolves taxonomic keys,
# filters by date span, and saves raw CSV.

library(rgbif)
library(dplyr)
library(lubridate)
library(here)
library(utils)

# Source utilities
source(here("src", "code", "utils.R"))

# --- Configuration ---
SPECIES_LIST_FILE <- here("data", "species_list.csv")
RAW_OUTPUT_DIR <- here("data", "raw")
OUTPUT_FILE <- here("data", "raw", "gbif_occurrences.csv")

# --- Helper Functions ---

resolve_taxonomic_key <- function(species_name) {
  # Uses rgbif::name_backbone to resolve a species name to a taxonKey
  # Returns the key or NA if resolution fails
  result <- tryCatch(
    {
      backbone <- name_backbone(name = species_name, rank = "species")
      if (length(backbone$taxonKey) > 0 && !is.na(backbone$taxonKey)) {
        return(backbone$taxonKey[1])
      }
      return(NA_integer_)
    },
    error = function(e) {
      log_warn(sprintf("Failed to resolve taxonomic key for %s: %s", species_name, e$message))
      return(NA_integer_)
    }
  )
  return(result)
}

filter_by_date_span <- function(df, min_years = 50) {
  # Filters records to ensure a span of at least 'min_years' between earliest and latest
  # Assumes 'eventDate' is present and parsable
  
  if (!"eventDate" %in% names(df)) {
    log_warn("eventDate column missing. Skipping date span filter.")
    return(df)
  }

  # Convert eventDate to Date (handling various formats)
  # GBIF often returns ISO 8601 or YYYY
  df <- df %>%
    mutate(
      parsed_date = as.Date(eventDate),
      year = year(parsed_date)
    )
  
  # Remove rows where date could not be parsed
  df <- df %>% filter(!is.na(year))
  
  # Calculate span per species
  spans <- df %>%
    group_by(species) %>%
    summarise(
      min_year = min(year, na.rm = TRUE),
      max_year = max(year, na.rm = TRUE),
      span = max_year - min_year,
      .groups = 'drop'
    ) %>%
    filter(span >= min_years)
  
  valid_species <- spans$species
  
  log_info(sprintf("Filtering: %d species have >= %d year span.", length(valid_species), min_years))
  
  return(df %>% filter(species %in% valid_species))
}

# --- Main Execution ---

main <- function() {
  log_info("Starting T006/T013: Fetch GBIF Data")
  
  # Ensure output directory exists
  ensure_dir(RAW_OUTPUT_DIR)
  
  # Load species list
  if (!file.exists(SPECIES_LIST_FILE)) {
    stop(sprintf("Species list file not found: %s", SPECIES_LIST_FILE))
  }
  
  species_list <- read.csv(SPECIES_LIST_FILE, stringsAsFactors = FALSE)
  if (!"species" %in% names(species_list)) {
    stop("Species list must contain a 'species' column.")
  }
  
  species_names <- unique(species_list$species)
  log_info(sprintf("Processing %d species.", length(species_names)))
  
  all_records <- list()
  
  for (sp in species_names) {
    log_info(sprintf("Querying GBIF for %s...", sp))
    
    # 1. Resolve Taxonomic Key
    taxon_key <- resolve_taxonomic_key(sp)
    
    if (is.na(taxon_key)) {
      log_warn(sprintf("Skipping %s: Could not resolve taxonomic key.", sp))
      next
    }
    
    # 2. Query GBIF
    # occurrenceStatus = "PRESERVED_SPECIMEN"
    # limit set to avoid timeouts (GBIF has a limit per request, usually 300, but we can paginate)
    # For this skeleton, we fetch up to 3000 records per species to ensure sufficient data
    tryCatch({
      result <- occ_search(
        taxonKey = taxon_key,
        occurrenceStatus = "PRESERVED_SPECIMEN",
        limit = 3000,
        return = "data"
      )
      
      if (length(result$data) > 0) {
        # Add species name column if not present (occ_search sometimes drops it if key is used)
        df <- result$data
        df$species <- sp
        
        # Filter for valid coordinates (basic check)
        df <- df %>%
          filter(!is.na(decimalLatitude), !is.na(decimalLongitude))
        
        all_records[[sp]] <- df
      } else {
        log_warn(sprintf("No records found for %s", sp))
      }
    }, error = function(e) {
      log_error(sprintf("Error querying GBIF for %s: %s", sp, e$message))
    })
  }
  
  if (length(all_records) == 0) {
    stop("No data retrieved for any species.")
  }
  
  # Combine all records
  combined_data <- bind_rows(all_records)
  
  log_info(sprintf("Total raw records retrieved: %d", nrow(combined_data)))
  
  # 3. Filter by Date Span
  filtered_data <- filter_by_date_span(combined_data, min_years = 50)
  
  log_info(sprintf("Records after date span filter: %d", nrow(filtered_data)))
  
  # 4. Save to CSV
  log_info(sprintf("Saving to %s", OUTPUT_FILE))
  write.csv(filtered_data, OUTPUT_FILE, row.names = FALSE)
  
  log_info("T006/T013 completed successfully.")
  
  return(invisible(TRUE))
}

if (!interactive()) {
  main()
}