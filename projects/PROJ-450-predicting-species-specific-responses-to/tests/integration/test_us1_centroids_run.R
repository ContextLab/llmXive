# Helper script to run the US1 pipeline before the integration test
# This ensures data exists for T012 to verify.
# This script is not a test itself, but a runner to be invoked by CI.

library(here)
library(dplyr)

# Source utils to ensure logging and directories are set up
source(here("src", "code", "utils.R"))

# Ensure directories
ensure_dir(here("data", "raw"))
ensure_dir(here("data", "processed"))

# Define test species
test_species <- c("Quercus robur", "Turdus merula")

# 1. Fetch
message("Running fetch_gbif for test species...")
# Note: This may take time. In CI, we might mock or use cached data.
# For this implementation, we assume the script exists and runs.
tryCatch({
  source(here("src", "code", "fetch_gbif.R"))
  fetch_gbif(species_list = test_species, output_dir = here("data", "raw"))
}, error = function(e) {
  message("Fetch step encountered an error (likely API limits): ", e$message)
})

# 2. Extract Climate
message("Running extract_climate...")
tryCatch({
  source(here("src", "code", "extract_climate.R"))
  extract_climate(input_dir = here("data", "raw"), output_dir = here("data", "processed"))
}, error = function(e) {
  message("Extract step encountered an error: ", e$message)
})

# 3. Compute Centroids
message("Running compute_centroids...")
tryCatch({
  source(here("src", "code", "compute_centroids.R"))
  compute_centroids(input_dir = here("data", "processed"), output_path = here("data", "processed", "centroids.csv"))
}, error = function(e) {
  message("Compute step encountered an error: ", e$message)
})

message("Pipeline run attempt complete. Check data/processed/ for output.")