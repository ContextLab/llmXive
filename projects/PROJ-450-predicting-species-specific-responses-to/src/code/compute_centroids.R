#!/usr/bin/env Rscript
# compute_centroids.R
# Task: T015a & T015b
# Description: Calculate arithmetic mean of climate variables per species/period
#              and output:
#              1. data/processed/centroids.csv (aggregated means)
#              2. data/processed/points_with_climate.csv (raw points with climate)
#
# Inputs:
#   - data/processed/points_with_climate.csv (from T014 extract_climate.R)
#
# Outputs:
#   - data/processed/centroids.csv
#   - data/processed/points_with_climate.csv (ensured to exist)

# Load project-wide utilities and configuration
# Assuming T004 utils.R is available in src/code/
source("src/code/utils.R")

# Ensure required directories exist
ensure_dir("data/processed")

# Define file paths
input_file <- "data/processed/points_with_climate.csv"
centroids_output <- "data/processed/centroids.csv"

# Check if input file exists
if (!file.exists(input_file)) {
  stop(paste("CRITICAL: Input file not found:", input_file, 
             "\nPlease run src/code/extract_climate.R (T014) first."))
}

log_info("Starting centroid computation...")
log_info(paste("Reading data from:", input_file))

# Read the raw occurrence data with climate values
# Expected columns: species, period, temp, precip, lat, lon, ...
tryCatch({
  df <- read.csv(input_file, stringsAsFactors = FALSE)
}, error = function(e) {
  stop(paste("Failed to read input CSV:", e$message))
})

log_info(paste("Loaded", nrow(df), "records."))

# Validate required columns
required_cols <- c("species", "period", "temp", "precip")
missing_cols <- setdiff(required_cols, names(df))
if (length(missing_cols) > 0) {
  stop(paste("Input file is missing required columns:", 
             paste(missing_cols, collapse = ", ")))
}

# Ensure numeric types for climate variables
df$temp <- as.numeric(df$temp)
df$precip <- as.numeric(df$precip)

# Filter out rows with NA climate values to ensure accurate means
# (Though T014 should have handled this, we double-check)
valid_rows <- complete.cases(df[, required_cols])
if (sum(!valid_rows) > 0) {
  log_warning(paste("Removing", sum(!valid_rows), 
                    "records with NA climate values."))
  df <- df[valid_rows, ]
}

# T015a: Calculate arithmetic mean of climate variables per species/period
log_info("Computing centroids (arithmetic means) per species and period...")

# Use base R aggregate to compute means
# Group by species and period, calculate mean of temp and precip
centroids <- aggregate(
  cbind(temp, precip) ~ species + period,
  data = df,
  FUN = mean,
  na.rm = TRUE
)

# Add metadata columns
centroids$computed_at <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
centroids$record_count <- ave(df$temp, df$species, df$period, FUN = length)

# Reorder columns for clarity
centroids <- centroids[, c("species", "period", "temp", "precip", "record_count", "computed_at")]

# Write centroids output
log_info(paste("Writing centroids to:", centroids_output))
write.csv(centroids, centroids_output, row.names = FALSE)

# Verify output
if (!file.exists(centroids_output)) {
  stop("Failed to write centroids output file.")
}

log_success(paste("Successfully generated", nrow(centroids), "centroid records."))

# T015b: Ensure points_with_climate.csv is written (as intermediate artifact)
# The input file is already points_with_climate.csv, but we ensure it is 
# explicitly written to the output location as required by the task spec.
log_info("Ensuring points_with_climate.csv is present as intermediate artifact...")
write.csv(df, input_file, row.names = FALSE)

log_success("Centroid computation and intermediate artifact generation complete.")

# Return invisible to allow sourcing
invisible(TRUE)
