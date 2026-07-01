#!/usr/bin/env Rscript
# compute_centroids.R
#
# Purpose:
#   1. Load raw occurrence data with climate values (from T014).
#   2. Compute arithmetic mean (centroid) of climate variables per species/period.
#   3. Output `centroids.csv` (aggregated means).
#   4. Output `points_with_climate.csv` (raw occurrence points with climate values)
#      as an intermediate artifact for FR-005 global z-scoring (T021).
#
# Inputs:
#   - data/processed/points_with_climate_temp_precip.csv (output of T014 extract_climate.R)
#
# Outputs:
#   - data/processed/centroids.csv (aggregated means per species/period)
#   - data/processed/points_with_climate.csv (raw points with climate values, copy/renamed)
#
# Dependencies:
#   - dplyr, readr, here, utils (from T002)
#   - src/code/utils.R (logging, validation from T004)

library(dplyr)
library(readr)
library(here)
library(lubridate)

# Source utility functions
source(here("src", "code", "utils.R"))

# Configuration
INPUT_FILE <- here("data", "processed", "points_with_climate_temp_precip.csv")
OUTPUT_CENTROIDS <- here("data", "processed", "centroids.csv")
OUTPUT_POINTS <- here("data", "processed", "points_with_climate.csv")

log_info("Starting compute_centroids.R")

# Check input file exists
if (!file.exists(INPUT_FILE)) {
  log_error(paste("Input file not found:", INPUT_FILE))
  stop("Input file missing. Run extract_climate.R first.")
}

log_info(paste("Loading data from:", INPUT_FILE))
df <- read_csv(INPUT_FILE, show_col_types = FALSE)

# Validate required columns
required_cols <- c("species", "period", "lat", "lon", "temp_mean", "precip_mean")
missing_cols <- setdiff(required_cols, names(df))
if (length(missing_cols) > 0) {
  log_error(paste("Missing required columns:", paste(missing_cols, collapse = ", ")))
  stop("Input data missing required columns.")
}

# Remove rows with NA in critical climate columns for centroid calculation
# (but keep them in the points output if needed for other reasons, though z-scoring will fail on NA)
# We will filter NA for centroid calculation to ensure valid means.
df_clean <- df %>%
  filter(!is.na(temp_mean) & !is.na(precip_mean))

log_info(paste("Records after NA removal for centroid calculation:", nrow(df_clean)))

# --- Task T015a: Compute Centroids ---
log_info("Computing centroids per species/period...")

centroids <- df_clean %>%
  group_by(species, period) %>%
  summarise(
    temp_mean_centroid = mean(temp_mean, na.rm = TRUE),
    precip_mean_centroid = mean(precip_mean, na.rm = TRUE),
    n_records = n(),
    .groups = "drop"
  )

# Ensure output directory exists
ensure_dir(here("data", "processed"))

# Write centroids
write_csv(centroids, OUTPUT_CENTROIDS)
log_info(paste("Centroids saved to:", OUTPUT_CENTROIDS))

# --- Task T015b: Output Raw Points with Climate ---
# The requirement is to output the raw occurrence points with climate values.
# The input file already contains this. We copy it to the specified output path
# to ensure the artifact exists at the expected location for downstream tasks (T021).
log_info("Preparing raw points with climate for FR-005 global z-scoring...")

# We use the cleaned version (NA removed) to ensure downstream z-scoring doesn't break on NAs,
# or we keep the original if the spec implies keeping all.
# FR-005 implies global z-scoring which typically requires complete cases.
# We will output the cleaned version to be safe for the next step,
# but label it clearly as the artifact for z-scoring.
# If the spec strictly wants *raw* (including NAs), we would copy `df`.
# However, "raw occurrence points with climate values" usually implies the result of the extraction.
# Given T021 needs this for z-scoring, we provide the clean version.
# To be strictly compliant with "raw", we will output the full dataframe `df` but
# note that downstream steps must handle NAs.
# Actually, looking at T021: "perform global z-scoring... from points_with_climate.csv".
# Z-scoring fails on NAs. So the artifact must be usable.
# Let's output the version with NAs removed to ensure the pipeline works,
# as "raw" in this context often means "un-aggregated" rather than "including errors".
# However, to be safest, I will output the version with NAs removed for the z-scoring task.
# If the user strictly wants the exact input copy, they can change this.
# Decision: Output the clean data to ensure T021 runs successfully.

# Re-reading T015b: "output `data/processed/points_with_climate.csv` (raw occurrence points with climate values)"
# It is an intermediate artifact specifically for FR-005.
# FR-005 says "global z-scoring". Z-scoring requires non-NA.
# So we output the clean version.

points_output <- df_clean %>%
  select(species, period, lat, lon, temp_mean, precip_mean)

write_csv(points_output, OUTPUT_POINTS)
log_info(paste("Raw points with climate saved to:", OUTPUT_POINTS))

log_info("compute_centroids.R completed successfully.")
log_info(paste("Output 1:", OUTPUT_CENTROIDS))
log_info(paste("Output 2:", OUTPUT_POINTS))