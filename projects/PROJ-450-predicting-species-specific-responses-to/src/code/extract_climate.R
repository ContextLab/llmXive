#!/usr/bin/env Rscript
# extract_climate.R
# Extracts mean annual temperature (°C) and precipitation (mm) from WorldClim v2
# rasters for occurrence points, handling two time periods: 1970-2000 and 1991-2020.
#
# Inputs:
#   - data/raw/occurrences.csv (output of T013/fetch_gbif.R)
#   - data/raw/worldclim_v2/*.tif (loaded by T007/download_worldclim.R)
# Outputs:
#   - data/processed/points_with_climate.csv (raw points with climate values)
#   - data/processed/centroids.csv (aggregated means per species/period)
#
# Dependencies:
#   - raster, sf, dplyr, tidyr, lubridate, here (installed via T002)

library(raster)
library(sf)
library(dplyr)
library(tidyr)
library(lubridate)
library(here)

source(here("src", "code", "utils.R"))

# --- Configuration ---
WORLDCLIM_DIR <- here("data", "raw", "worldclim_v2")
INPUT_CSV <- here("data", "raw", "occurrences.csv")
OUTPUT_POINTS <- here("data", "processed", "points_with_climate.csv")
OUTPUT_CENTROIDS <- here("data", "processed", "centroids.csv")

# Period definitions (matching WorldClim v2 naming conventions)
# WorldClim v2.1 uses: bio1 (annual mean temp) and bio12 (annual precip)
# Layers are named: bio1_1970.tif, bio12_1970.tif, bio1_1991.tif, bio12_1991.tif
# Note: Adjust names if T007 downloads different filenames.
TEMP_1970 <- "bio1_1970.tif"
PRECIP_1970 <- "bio12_1970.tif"
TEMP_1991 <- "bio1_1991.tif"
PRECIP_1991 <- "bio12_1991.tif"

# --- Helper Functions ---

load_raster_stack <- function(temp_file, precip_file, period_label) {
  temp_path <- file.path(WORLDCLIM_DIR, temp_file)
  precip_path <- file.path(WORLDCLIM_DIR, precip_file)

  if (!file.exists(temp_path) || !file.exists(precip_path)) {
    stop(sprintf("Missing WorldClim layers for %s: %s or %s",
                 period_label, temp_path, precip_path))
  }

  temp_raster <- raster(temp_path)
  precip_raster <- raster(precip_path)

  # Ensure same CRS (WorldClim is usually WGS84)
  if (crs(temp_raster) != crs(precip_raster)) {
    stop("Temperature and precipitation rasters have different CRS.")
  }

  stack(temp_raster, precip_raster)
}

extract_climate_for_points <- function(points_df, raster_stack, period_label) {
  # Convert data.frame to sf object
  pts_sf <- st_as_sf(points_df, coords = c("decimalLongitude", "decimalLatitude"), crs = 4326)

  # Extract values
  # extract returns a matrix or vector; handle NA carefully
  vals <- extract(raster_stack, pts_sf)

  if (is.null(vals)) {
    # No points extracted (all NA or out of bounds)
    climate_df <- data.frame(
      period = period_label,
      temp_C = NA_real_,
      precip_mm = NA_real_,
      stringsAsFactors = FALSE
    )
  } else {
    # vals is a matrix with 2 columns: temp, precip
    climate_df <- data.frame(
      period = period_label,
      temp_C = vals[, 1],
      precip_mm = vals[, 2],
      stringsAsFactors = FALSE
    )
  }

  # Bind back to original points (keeping original columns)
  result <- cbind(points_df, climate_df)

  # Log NA handling
  na_temp_count <- sum(is.na(result$temp_C))
  na_precip_count <- sum(is.na(result$precip_mm))
  log_info(sprintf("Extracted climate for %s: %d NA temp, %d NA precip.",
                   period_label, na_temp_count, na_precip_count))

  result
}

compute_centroids <- function(points_with_climate_df) {
  # Group by species and period, calculate arithmetic mean of climate variables
  # Handle NA: mean(..., na.rm = TRUE)
  centroids <- points_with_climate_df %>%
    group_by(species, period) %>%
    summarise(
      mean_temp_C = mean(temp_C, na.rm = TRUE),
      mean_precip_mm = mean(precip_mm, na.rm = TRUE),
      count = n(),
      .groups = "drop"
    )

  # Filter out groups where all values were NA (count > 0 but means are NA)
  centroids <- centroids %>%
    filter(!is.na(mean_temp_C) & !is.na(mean_precip_mm))

  log_info(sprintf("Computed centroids for %d species/period combinations.", nrow(centroids)))
  centroids
}

# --- Main Execution ---

main <- function() {
  log_start("extract_climate")

  # Ensure output directory exists
  ensure_dir(here("data", "processed"))

  # Load input data
  log_info("Loading occurrence data from %s", INPUT_CSV)
  if (!file.exists(INPUT_CSV)) {
    stop(sprintf("Input file not found: %s. Run T013 first.", INPUT_CSV))
  }
  occ_data <- read.csv(INPUT_CSV, stringsAsFactors = FALSE)

  # Validate required columns
  required_cols <- c("species", "decimalLongitude", "decimalLatitude")
  missing_cols <- setdiff(required_cols, names(occ_data))
  if (length(missing_cols) > 0) {
    stop(sprintf("Missing required columns in input: %s", paste(missing_cols, collapse = ", ")))
  }

  # Process 1970-2000
  log_info("Processing 1970-2000 period...")
  stack_1970 <- load_raster_stack(TEMP_1970, PRECIP_1970, "1970-2000")
  points_1970 <- extract_climate_for_points(occ_data, stack_1970, "1970-2000")

  # Process 1991-2020
  log_info("Processing 1991-2020 period...")
  stack_1991 <- load_raster_stack(TEMP_1991, PRECIP_1991, "1991-2020")
  points_1991 <- extract_climate_for_points(occ_data, stack_1991, "1991-2020")

  # Combine results
  all_points <- bind_rows(points_1970, points_1991)

  # Write raw points with climate
  write.csv(all_points, OUTPUT_POINTS, row.names = FALSE)
  log_info("Saved points with climate to %s", OUTPUT_POINTS)

  # Compute and write centroids
  centroids <- compute_centroids(all_points)
  write.csv(centroids, OUTPUT_CENTROIDS, row.names = FALSE)
  log_info("Saved centroids to %s", OUTPUT_CENTROIDS)

  log_end("extract_climate")
}

# Run main if executed as script
if (!interactive()) {
  main()
}
