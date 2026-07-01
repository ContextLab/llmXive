#!/usr/bin/env Rscript
# download_worldclim.R
# Checks for local WorldClim v2 rasters. If missing, downloads them from WorldClim.
# Verifies checksums (if available) and saves to data/raw/.
#
# Outputs:
#   - data/raw/worldclim_v2/*.tif
#
# Dependencies:
#   - raster, curl, here

library(raster)
library(here)

source(here("src", "code", "utils.R"))

# --- Configuration ---
OUTPUT_DIR <- here("data", "raw", "worldclim_v2")
BASE_URL_1970 <- "https://worldclim.org/data/bioclim_1970-2000.html" # Placeholder for actual download links
# Actual WorldClim v2.1 download links are complex. We will use a direct link pattern or a package if available.
# For this task, we assume direct download of specific bio1 and bio12.
# WorldClim v2.1 Global Bioclimatic Variables (1970-2000 and 1991-2020)
# URLs (example for bio1, bio12):
# 1970-2000: https://biogeo.ucdavis.edu/data/worldclim/v2.1/bio/wcs_1970_2000_v2.1.zip (requires unzip)
# Or individual tifs: https://biogeo.ucdavis.edu/data/worldclim/v2.1/bio/v21_bio1_1970.tif
# We will use the direct tif links for bio1 and bio12.

FILES_TO_DOWNLOAD <- list(
  list(name = "bio1_1970.tif", url = "https://biogeo.ucdavis.edu/data/worldclim/v2.1/bio/v21_bio1_1970.tif"),
  list(name = "bio12_1970.tif", url = "https://biogeo.ucdavis.edu/data/worldclim/v2.1/bio/v21_bio12_1970.tif"),
  list(name = "bio1_1991.tif", url = "https://biogeo.ucdavis.edu/data/worldclim/v2.1/bio/v21_bio1_1991.tif"),
  list(name = "bio12_1991.tif", url = "https://biogeo.ucdavis.edu/data/worldclim/v2.1/bio/v21_bio12_1991.tif")
)

# --- Helper Functions ---

download_file <- function(url, dest) {
  log_info("Downloading %s from %s", basename(dest), url)
  tryCatch({
    utils::download.file(url, destfile = dest, mode = "wb", quiet = TRUE)
    if (file.exists(dest) && file.info(dest)$size > 0) {
      log_info("Downloaded %s successfully.", basename(dest))
      return(TRUE)
    } else {
      log_warn("Downloaded file %s is empty or missing.", basename(dest))
      return(FALSE)
    }
  }, error = function(e) {
    log_error("Failed to download %s: %s", basename(dest), e$message)
    return(FALSE)
  })
}

# --- Main Execution ---

main <- function() {
  log_start("download_worldclim")
  ensure_dir(OUTPUT_DIR)

  all_downloaded <- TRUE

  for (file_info in FILES_TO_DOWNLOAD) {
    dest_path <- file.path(OUTPUT_DIR, file_info$name)

    if (file.exists(dest_path)) {
      log_info("File already exists: %s", file_info$name)
      # Optional: Verify checksum if we had a manifest
    } else {
      success <- download_file(file_info$url, dest_path)
      if (!success) {
        all_downloaded <- FALSE
      }
    }
  }

  if (all_downloaded) {
    log_info("All WorldClim layers present in %s", OUTPUT_DIR)
  } else {
    log_warn("Some layers failed to download. Check logs.")
  }

  log_end("download_worldclim")
}

if (!interactive()) {
  main()
}