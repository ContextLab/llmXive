#!/usr/bin/env Rscript
# compute_centroids.R
#
# Purpose:
#   1. Read raw occurrence data with climate values (from extract_climate.R).
#   2. Compute arithmetic mean (centroid) of climate variables per species/period.
#   3. Output two files:
#      - data/processed/centroids.csv (aggregated means)
#      - data/processed/points_with_climate.csv (raw points with climate values, for FR-005)
#
# Inputs:
#   - data/processed/points_with_climate_raw.csv (output of extract_climate.R)
#
# Outputs:
#   - data/processed/centroids.csv
#   - data/processed/points_with_climate.csv (re-validated and saved as intermediate artifact)

# Load project utilities
source("src/code/utils.R")

# --- Configuration ---
INPUT_FILE <- "data/processed/points_with_climate_raw.csv"
OUTPUT_CENTROIDS <- "data/processed/centroids.csv"
OUTPUT_POINTS <- "data/processed/points_with_climate.csv"

# Ensure output directory exists
ensure_dir("data/processed")

# --- Logging ---
log_start("compute_centroids")
log_info(paste("Input file:", INPUT_FILE))

# --- Check Input ---
if (!file.exists(INPUT_FILE)) {
  log_error("Input file not found: ", INPUT_FILE)
  log_error("Please run src/code/extract_climate.R first.")
  stop("Missing input file for compute_centroids.R")
}

# --- Load Data ---
log_info("Loading raw occurrence data with climate values...")
df_raw <- tryCatch({
  read.csv(INPUT_FILE, stringsAsFactors = FALSE)
}, error = function(e) {
  log_error("Failed to read input file: ", e$message)
  stop(e)
})

# Validate expected columns
required_cols <- c("species", "period", "temp_mean", "precip_mean", "latitude", "longitude")
missing_cols <- setdiff(required_cols, names(df_raw))
if (length(missing_cols) > 0) {
  log_error("Missing required columns in input: ", paste(missing_cols, collapse = ", "))
  stop("Input file missing required columns.")
}

# --- Data Cleaning & Validation ---
log_info("Validating data integrity...")

# Filter out rows with missing climate values (NA) as per data hygiene requirements
initial_count <- nrow(df_raw)
df_clean <- df_raw[!is.na(df_raw$temp_mean) & !is.na(df_raw$precip_mean), ]
filtered_count <- initial_count - nrow(df_clean)

if (filtered_count > 0) {
  log_warn(paste("Filtered out", filtered_count, "rows due to NA climate values."))
}

# Filter out rows with invalid coordinates (NA or outside reasonable bounds)
df_clean <- df_clean[!is.na(df_clean$latitude) & !is.na(df_clean$longitude), ]
after_coord_filter <- nrow(df_clean)
coord_filtered <- nrow(df_clean) - after_coord_filter

if (coord_filtered > 0) {
  log_warn(paste("Filtered out", coord_filtered, "rows due to invalid coordinates."))
}

# Ensure coordinates are within valid ranges
df_clean <- df_clean[df_clean$latitude >= -90 & df_clean$latitude <= 90, ]
df_clean <- df_clean[df_clean$longitude >= -180 & df_clean$longitude <= 180, ]
final_count <- nrow(df_clean)

log_info(paste("Total records processed:", initial_count))
log_info(paste("Records after cleaning:", final_count))

if (final_count == 0) {
  log_error("No valid records remaining after cleaning.")
  stop("No valid data to process.")
}

# --- Output 1: Save Raw Points with Climate (Intermediate Artifact for FR-005) ---
log_info("Saving intermediate artifact: points_with_climate.csv")

# Select specific columns for the output to ensure consistency
points_output <- df_clean[, c("species", "period", "latitude", "longitude", "temp_mean", "precip_mean")]

tryCatch({
  write.csv(points_output, OUTPUT_POINTS, row.names = FALSE)
  log_info(paste("Successfully saved", nrow(points_output), "records to", OUTPUT_POINTS))
}, error = function(e) {
  log_error("Failed to write points_with_climate.csv: ", e$message)
  stop(e)
})

# --- Output 2: Compute Centroids (Aggregated Means) ---
log_info("Computing centroids per species and period...")

# Group by species and period, calculate mean of temp and precip
centroids_list <- list()

unique_species <- unique(df_clean$species)
unique_periods <- unique(df_clean$period)

results <- data.frame(
  species = character(),
  period = character(),
  temp_mean_centroid = numeric(),
  precip_mean_centroid = numeric(),
  record_count = integer(),
  stringsAsFactors = FALSE
)

for (sp in unique_species) {
  for (per in unique_periods) {
    subset_data <- df_clean[df_clean$species == sp & df_clean$period == per, ]
    
    if (nrow(subset_data) > 0) {
      temp_mean_val <- mean(subset_data$temp_mean, na.rm = TRUE)
      precip_mean_val <- mean(subset_data$precip_mean, na.rm = TRUE)
      
      results <- rbind(results, data.frame(
        species = sp,
        period = per,
        temp_mean_centroid = temp_mean_val,
        precip_mean_centroid = precip_mean_val,
        record_count = nrow(subset_data),
        stringsAsFactors = FALSE
      ))
    } else {
      log_warn(paste("No data found for species:", sp, "period:", per))
    }
  }
}

# Write Centroids CSV
tryCatch({
  write.csv(results, OUTPUT_CENTROIDS, row.names = FALSE)
  log_info(paste("Successfully saved", nrow(results), "centroids to", OUTPUT_CENTROIDS))
}, error = function(e) {
  log_error("Failed to write centroids.csv: ", e$message)
  stop(e)
})

# --- Final Logging ---
log_info("compute_centroids.R completed successfully.")
log_info(paste("Output files:", OUTPUT_CENTROIDS, "and", OUTPUT_POINTS))

# Return invisible for sourcing
invisible(results)
