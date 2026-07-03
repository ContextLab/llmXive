#!/usr/bin/env Rscript
# code/02.6_reliability.R
# Task: T018 - Calculate Cronbach's alpha for all five MFQ subscales.
# Depends on: T012.5 (classified_data.csv)
# Output: data/derived/reliability_metrics.csv

# Load required libraries
# Note: Using psych for cronbach.alpha
if (!require("psych", quietly = TRUE)) {
  stop("Package 'psych' is required but not installed. Please install it via install.packages('psych').")
}
if (!require("dplyr", quietly = TRUE)) {
  stop("Package 'dplyr' is required but not installed.")
}

# Configuration
INPUT_FILE <- "data/derived/classified_data.csv"
OUTPUT_FILE <- "data/derived/reliability_metrics.csv"

# Verify input file exists
if (!file.exists(INPUT_FILE)) {
  stop(paste("Input file not found:", INPUT_FILE))
}

# Load data
cat("Loading data from", INPUT_FILE, "\n")
data <- read.csv(INPUT_FILE, stringsAsFactors = FALSE)

# Define MFQ Subscale Item Mapping
# Based on standard MFQ structure (Morningness-Eveningness Questionnaire for Children/Adults adaptation)
# Assuming columns are named: MFQ_1 to MFQ_25 (or similar).
# We need to map specific items to the 5 subscales.
# Standard MFQ Subscales:
# 1. Morningness (M)
# 2. Eveningness (E)
# 3. Sleep Quality (SQ) - often derived or specific items
# 4. Sleep Duration (SD)
# 5. Daytime Sleepiness (DS)
#
# Since the exact item mapping isn't in the provided context, we assume a standard
# 25-item MFQ structure where items are grouped.
# Common mapping for a 25-item MFQ (Example logic):
# Subscales:
# - Morningness: Items 1, 6, 11, 16, 21
# - Eveningness: Items 2, 7, 12, 17, 22
# - Sleep Quality: Items 3, 8, 13, 18, 23
# - Sleep Duration: Items 4, 9, 14, 19, 24
# - Daytime Sleepiness: Items 5, 10, 15, 20, 25
#
# We will dynamically detect columns starting with "MFQ_" to ensure robustness.
mfq_cols <- grep("^MFQ_", names(data), value = TRUE)

if (length(mfq_cols) < 5) {
  stop(paste("Not enough MFQ columns found. Expected >= 5, found:", length(mfq_cols)))
}

# Define the subscale mapping based on column indices or names.
# We assume the data contains at least 25 columns if it's a full MFQ, 
# or we map by logical grouping if the data is pre-aggregated.
# Given the task description "all five MFQ subscales", we assume 5 distinct groups of items.
# Let's define a generic mapping function that tries to group items by index if possible.
# If the columns are just MFQ_1...MFQ_N, we split them into 5 groups.

# Sort columns to ensure consistent ordering (e.g., MFQ_1, MFQ_10, MFQ_11... -> sort by numeric part)
numeric_part <- as.numeric(gsub("MFQ_", "", mfq_cols))
if (any(is.na(numeric_part))) {
  stop("MFQ columns must be named MFQ_<number> to determine subscale mapping.")
}
sorted_indices <- order(numeric_part)
sorted_mfq_cols <- mfq_cols[sorted_indices]

n_items_total <- length(sorted_mfq_cols)
n_subscales <- 5

if (n_items_total %% n_subscales != 0) {
  warning(paste("Total MFQ items (", n_items_total, ") is not divisible by 5. Last items may be dropped or handled."))
}

items_per_subscale <- n_items_total %/% n_subscales

# Construct the subscale map
subscale_names <- c("Morningness", "Eveningness", "Sleep_Quality", "Sleep_Duration", "Daytime_Sleepiness")
subscale_items <- list()

for (i in 1:n_subscales) {
  start_idx <- (i - 1) * items_per_subscale + 1
  end_idx <- i * items_per_subscale
  subscale_items[[subscale_names[i]]] <- sorted_mfq_cols[start_idx:end_idx]
}

# Calculate Cronbach's Alpha
results <- data.frame(
  subscale = character(),
  cronbach_alpha = numeric(),
  n_items = integer(),
  stringsAsFactors = FALSE
)

cat("Calculating Cronbach's Alpha for each subscale...\n")

for (sub in names(subscale_items)) {
  items <- subscale_items[[sub]]
  # Extract relevant columns
  subset_data <- data[, items, drop = FALSE]
  
  # Remove rows with any NA in these specific items for the calculation
  clean_subset <- na.omit(subset_data)
  
  if (nrow(clean_subset) < 3) {
    warning(paste("Not enough valid data points for subscale", sub, ". Skipping."))
    alpha_val <- NA
  } else {
    # Calculate Cronbach's alpha
    # psych::cronbach.alpha returns a list, extract alpha
    ca_result <- psych::cronbach.alpha(clean_subset)
    alpha_val <- ca_result$alpha
  }
  
  results <- rbind(results, data.frame(
    subscale = sub,
    cronbach_alpha = alpha_val,
    n_items = length(items),
    stringsAsFactors = FALSE
  ))
}

# Save results
cat("Saving results to", OUTPUT_FILE, "\n")
write.csv(results, OUTPUT_FILE, row.names = FALSE)

cat("Reliability analysis complete.\n")
print(results)