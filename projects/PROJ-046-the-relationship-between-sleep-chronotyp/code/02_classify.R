#!/usr/bin/env Rscript

# Task T012: Classify Chronotype based on MEQ and MFQ scores
# Depends on: T005 (scoring docs), T011 (cleaned_data.csv)
# Output: data/derived/classified_data.csv, logs/classify_exclusions.log

library(tidyverse)
library(data.table)
library(lubridate)

# Source configuration for paths
source("code/00_config.R")

# --- Configuration ---
INPUT_FILE <- file.path(OUTPUT_DIR_PROCESSED, "cleaned_data.csv")
OUTPUT_FILE <- file.path(OUTPUT_DIR_DERIVED, "classified_data.csv")
LOG_FILE <- file.path(LOGS_DIR, "classify_exclusions.log")

# Thresholds defined in T005 (Constitution Principle VI)
# MEQ >= 59 -> "morning"
# MEQ <= 41 -> "evening"
# Else -> "intermediate"
MEQ_THRESHOLD_MORNING <- 59
MEQ_THRESHOLD_EVENING <- 41

# MFQ Valid Ranges (per FR-006, typical 0-4 or 0-5 Likert, checking for NA/outliers)
# We assume MFQ items are named MFQ_1 to MFQ_22 (standard 22 items) or similar.
# T005 specifies exact item ordering. We will check for any non-numeric or extreme outliers.
# Assuming standard 1-5 Likert scale. Outliers defined as < 1 or > 5.
MFQ_MIN_VAL <- 0
MFQ_MAX_VAL <- 6

# --- Logging Setup ---
log_message <- function(msg) {
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  log_entry <- sprintf("[%s] %s", timestamp, msg)
  cat(log_entry, "\n", file = LOG_FILE, append = TRUE)
}

# Ensure log directory exists
if (!dir.exists(LOGS_DIR)) {
  dir.create(LOGS_DIR, recursive = TRUE)
}

# Clear previous log for this run (optional, but keeps log clean per run)
# We append, so we log the start of the run.
log_message("Starting classification pipeline (T012).")

# --- Load Data ---
if (!file.exists(INPUT_FILE)) {
  stop("Input file not found: ", INPUT_FILE)
}

data <- fread(INPUT_FILE)
original_n <- nrow(data)
log_message(sprintf("Loaded %d rows from %s", original_n, INPUT_FILE))

# Identify MFQ columns dynamically
mfq_cols <- grep("^MFQ_", names(data), value = TRUE)
if (length(mfq_cols) == 0) {
  stop("No MFQ columns found in input data. Expected columns starting with 'MFQ_'.")
}
log_message(sprintf("Identified %d MFQ columns: %s", length(mfq_cols), paste(mfq_cols, collapse = ", ")))

# --- Validation & Filtering ---
exclusion_indices <- c()
exclusion_reasons <- character()

# 1. Check MEQ_score validity
if (!("MEQ_score" %in% names(data))) {
  stop("Required column 'MEQ_score' not found in input data.")
}

# Rows with NA or non-numeric MEQ_score
meq_na <- is.na(data$MEQ_score)
meq_non_numeric <- !is.numeric(data$MEQ_score)
# In R fread, numeric columns are usually numeric, but let's be safe if mixed types exist
# If the column is character, try to parse, else flag as error
if (is.character(data$MEQ_score)) {
  # Attempt conversion
  parsed_meq <- suppressWarnings(as.numeric(data$MEQ_score))
  meq_non_numeric <- is.na(parsed_meq)
}

invalid_meq <- meq_na | meq_non_numeric

if (sum(invalid_meq) > 0) {
  exclusion_indices <- c(exclusion_indices, which(invalid_meq))
  exclusion_reasons <- c(exclusion_reasons, rep("Invalid MEQ_score (NA or non-numeric)", sum(invalid_meq)))
  log_message(sprintf("Excluding %d rows due to Invalid MEQ_score.", sum(invalid_meq)))
}

# 2. Check MFQ out-of-range scores (FR-006)
# We check each MFQ column for values outside [MFQ_MIN_VAL, MFQ_MAX_VAL]
# If ANY item in a row is out of range, exclude the row.
mfq_invalid_rows <- rep(FALSE, nrow(data))

for (col in mfq_cols) {
  # Ensure numeric
  if (!is.numeric(data[[col]])) {
     data[[col]] <- suppressWarnings(as.numeric(data[[col]]))
  }
  # Check range
  invalid_vals <- data[[col]] < MFQ_MIN_VAL | data[[col]] > MFQ_MAX_VAL
  mfq_invalid_rows <- mfq_invalid_rows | invalid_vals
}

# Exclude rows that are not already excluded and have invalid MFQ
new_exclusions <- mfq_invalid_rows & !invalid_meq
if (sum(new_exclusions) > 0) {
  exclusion_indices <- c(exclusion_indices, which(new_exclusions))
  exclusion_reasons <- c(exclusion_reasons, rep("Out-of-range MFQ score", sum(new_exclusions)))
  log_message(sprintf("Excluding %d rows due to Out-of-range MFQ score.", sum(new_exclusions)))
}

# Remove duplicates in exclusion indices just in case
exclusion_indices <- unique(exclusion_indices)
total_excluded <- length(exclusion_indices)

# --- Classification Logic ---
if (total_excluded > 0) {
  data <- data[-exclusion_indices, ]
  log_message(sprintf("Total rows excluded: %d. Remaining rows: %d", total_excluded, nrow(data)))
} else {
  log_message("No rows excluded.")
}

# Apply Chronotype Thresholds
data <- data %>%
  mutate(
    chronotype = case_when(
      is.na(MEQ_score) ~ NA_character_, # Should be handled by exclusion, but safety check
      MEQ_score >= MEQ_THRESHOLD_MORNING ~ "morning",
      MEQ_score <= MEQ_THRESHOLD_EVENING ~ "evening",
      TRUE ~ "intermediate"
    )
  )

# Verify classification
if (any(is.na(data$chronotype))) {
  log_message("Warning: Some rows still have NA chronotype after classification.")
}

# --- Save Output ---
# Ensure output directory exists
if (!dir.exists(OUTPUT_DIR_DERIVED)) {
  dir.create(OUTPUT_DIR_DERIVED, recursive = TRUE)
}

fwrite(data, OUTPUT_FILE)
log_message(sprintf("Saved classified data to %s (%d rows)", OUTPUT_FILE, nrow(data)))

# Log summary
chronotype_counts <- table(data$chronotype, useNA = "ifany")
log_message("Classification Summary:")
for (i in seq_along(chronotype_counts)) {
  log_message(sprintf("  %s: %d", names(chronotype_counts)[i], chronotype_counts[i]))
}

log_message("Classification pipeline (T012) completed successfully.")
cat(sprintf("Classification complete. Output: %s\n", OUTPUT_FILE))
cat(sprintf("Exclusions logged: %s\n", LOG_FILE))
