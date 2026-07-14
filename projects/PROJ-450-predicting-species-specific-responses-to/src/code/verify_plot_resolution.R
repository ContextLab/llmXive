#!/usr/bin/env Rscript
# Task T037: Verify all PNG plots meet 1200x800px resolution requirement (SC-004)
#
# This script scans the 'figures/' directory for all .png files,
# reads their dimensions using the 'imager' or 'png' package,
# and verifies that width >= 1200 and height >= 800.
# It outputs a summary CSV to 'results/plot_resolution_check.csv'
# and exits with status 1 if any plot fails the check.

library(here)
library(dplyr)
library(png)
library(tidyr)

# Configuration
FIGURES_DIR <- here("figures")
RESULTS_DIR <- here("results")
OUTPUT_FILE <- here("results", "plot_resolution_check.csv")

# Ensure results directory exists
if (!dir.exists(RESULTS_DIR)) {
  dir.create(RESULTS_DIR, recursive = TRUE)
}

# Check if figures directory exists
if (!dir.exists(FIGURES_DIR)) {
  warning("No 'figures/' directory found. Creating empty results.")
  results_df <- data.frame(
    file = character(0),
    width = integer(0),
    height = integer(0),
    status = character(0),
    message = character(0)
  )
  write.csv(results_df, OUTPUT_FILE, row.names = FALSE)
  cat("No figures found. Results saved to", OUTPUT_FILE, "\n")
  quit(status = 0)
}

# Get list of PNG files
png_files <- list.files(FIGURES_DIR, pattern = "\\.png$", full.names = TRUE, ignore.case = TRUE)

if (length(png_files) == 0) {
  warning("No .png files found in 'figures/'. Creating empty results.")
  results_df <- data.frame(
    file = character(0),
    width = integer(0),
    height = integer(0),
    status = character(0),
    message = character(0)
  )
  write.csv(results_df, OUTPUT_FILE, row.names = FALSE)
  cat("No PNG files found. Results saved to", OUTPUT_FILE, "\n")
  quit(status = 0)
}

cat("Scanning", length(png_files), "PNG files for resolution compliance...\n")

results <- lapply(png_files, function(f) {
  tryCatch({
    img <- readPNG(f)
    # readPNG returns a 3D array (height, width, channels)
    h <- dim(img)[1]
    w <- dim(img)[2]

    # Check against requirements (SC-004: >= 1200x800)
    pass <- (w >= 1200) && (h >= 800)
    status <- if (pass) "PASS" else "FAIL"
    msg <- if (pass) "Meets requirement" else sprintf("Too small: %dx%d (min 1200x800)", w, h)

    data.frame(
      file = basename(f),
      width = w,
      height = h,
      status = status,
      message = msg,
      stringsAsFactors = FALSE
    )
  }, error = function(e) {
    data.frame(
      file = basename(f),
      width = NA_integer_,
      height = NA_integer_,
      status = "ERROR",
      message = sprintf("Failed to read: %s", e$message),
      stringsAsFactors = FALSE
    )
  })
})

results_df <- bind_rows(results)

# Write results
write.csv(results_df, OUTPUT_FILE, row.names = FALSE)

# Print summary
cat("\n--- Resolution Verification Summary ---\n")
print(results_df)
cat("\n")

fail_count <- sum(results_df$status == "FAIL", na.rm = TRUE)
error_count <- sum(results_df$status == "ERROR", na.rm = TRUE)

if (fail_count > 0 || error_count > 0) {
  cat(sprintf("FAILED: %d plots did not meet resolution requirements.", fail_count + error_count))
  cat(sprintf(" Details saved to: %s\n", OUTPUT_FILE))
  quit(status = 1)
} else {
  cat("SUCCESS: All PNG plots meet the 1200x800px resolution requirement.\n")
  quit(status = 0)
}
