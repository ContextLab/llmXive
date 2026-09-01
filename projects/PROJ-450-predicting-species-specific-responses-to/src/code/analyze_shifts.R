# src/code/analyze_shifts.R
# Analyze niche shifts (Delta N) against regional warming (Delta T)
# Implements PGLS if phylogeny available, otherwise WLS.
# Includes detailed logging per FR-010.

library(caper)
library(phylolm)
library(dplyr)
library(tidyr)
library(lubridate)
library(here)
library(ggplot2)

# Source utility functions (logging, directory checks)
source(here("src", "code", "utils.R"))

# Configuration
log_file <- here("logs", "analysis_shifts.log")
input_shifts <- here("data", "processed", "shifts.csv")
input_centroids <- here("data", "processed", "centroids.csv")
phylogeny_file <- here("data", "phylogeny.tre")
output_results <- here("results", "regression_summary.csv")
output_regions <- here("results", "regional_regression_summary.csv")

# Initialize logging
init_logging(log_file)
log_message(paste("Starting analysis for", Sys.time()))

# Check inputs
if (!file.exists(input_shifts)) {
  log_error("Input file not found: shifts.csv. Run compute_shifts.R first.")
  stop("Missing input: shifts.csv")
}

log_message(paste("Loading data from", input_shifts))
shifts_df <- read.csv(input_shifts, stringsAsFactors = FALSE)

# Validate required columns
required_cols <- c("species", "delta_N", "delta_T", "taxonomic_group")
if (!all(required_cols %in% names(shifts_df))) {
  missing <- setdiff(required_cols, names(shifts_df))
  log_error(paste("Missing columns in shifts.csv:", paste(missing, collapse=", ")))
  stop("Invalid shifts.csv schema")
}

log_message(paste("Loaded", nrow(shifts_df), "species records for analysis"))

# Determine method: PGLS or WLS
use_pgl <- FALSE
if (file.exists(phylogeny_file)) {
  log_message("Phylogeny file detected. Attempting PGLS.")
  tryCatch({
    tree <- read.tree(phylogeny_file)
    if (!is.null(tree) && length(tree$tip.label) > 0) {
      use_pgl <- TRUE
      log_message(paste("Loaded phylogeny with", length(tree$tip.label), "tips."))
    }
  }, error = function(e) {
    log_warning(paste("Failed to load phylogeny:", e$message, "Falling back to WLS."))
    use_pgl <- FALSE
  })
} else {
  log_message("No phylogeny file found. Using WLS (Weighted Least Squares).")
}

# --- Global Regression ---
log_message("Starting global regression analysis.")

# Clean data for regression (remove NAs in dependent variables)
clean_data <- shifts_df %>%
  filter(!is.na(delta_N), !is.na(delta_T))

if (nrow(clean_data) < 2) {
  log_error("Insufficient data points for regression (need >= 2).")
  stop("Not enough valid data points")
}

log_message(paste("Running regression on", nrow(clean_data), "valid points."))

global_result <- NULL
if (use_pgl) {
  # Prepare data for caper (requires species matching tree)
  # Note: In a real scenario, we might need to prune the tree or data
  # to match. Here we assume taxon names match tip labels.
  tryCatch({
    tree <- read.tree(phylogeny_file)
    # Prune tree to match data
    common_tips <- intersect(tree$tip.label, clean_data$species)
    if (length(common_tips) < 2) {
      log_warning("Few matching species between data and tree. Using WLS fallback.")
      use_pgl <- FALSE
      stop("Mismatch")
    }
    tree_pruned <- keep.tip(tree, common_tips)
    data_pruned <- clean_data %>% filter(species %in% common_tips)
    rownames(data_pruned) <- data_pruned$species

    comp_data <- comparative.data(tree_pruned, data_pruned, names.col = "species", v = TRUE, warn = FALSE)

    model <- pgls(delta_N ~ delta_T, data = comp_data, lambda = "ML")
    global_result <- list(
      method = "PGLS",
      slope = coef(model)[2],
      ci_lower = confint(model)[2, 1],
      ci_upper = confint(model)[2, 2],
      r_squared = summary(model)$r.squared,
      p_value = summary(model)$coefficients[2, 4]
    )
    log_message("PGLS regression completed successfully.")
  }, error = function(e) {
    log_warning(paste("PGLS failed:", e$message, "Falling back to WLS."))
    use_pgl <- FALSE
  })
}

if (!use_pgl) {
  # WLS Fallback
  log_message("Running WLS regression.")
  model <- lm(delta_N ~ delta_T, data = clean_data)
  summ <- summary(model)
  global_result <- list(
    method = "WLS",
    slope = coef(model)[2],
    ci_lower = summ$coefficients[2, 1] - 1.96 * summ$coefficients[2, 2],
    ci_upper = coef(model)[2] + 1.96 * summ$coefficients[2, 2],
    r_squared = summ$r.squared,
    p_value = summ$coefficients[2, 4]
  )
  log_message("WLS regression completed successfully.")
}

# Log Global Results
log_message(paste("Global Regression Results (", global_result$method, "):", sep=""))
log_message(paste("  Slope:", round(global_result$slope, 4)))
log_message(paste("  95% CI: [", round(global_result$ci_lower, 4), ", ", round(global_result$ci_upper, 4), "]"))
log_message(paste("  R-squared:", round(global_result$r_squared, 4)))
log_message(paste("  P-value:", format.pval(global_result$p_value)))

# Save Global Results
global_df <- data.frame(
  analysis_type = "Global",
  method = global_result$method,
  slope = global_result$slope,
  ci_lower = global_result$ci_lower,
  ci_upper = global_result$ci_upper,
  r_squared = global_result$r_squared,
  p_value = global_result$p_value
)

write.csv(global_df, output_results, row.names = FALSE)
log_message(paste("Global results saved to", output_results))

# --- Per-Region Analysis (Latitudinal Bands) ---
log_message("Starting per-region analysis (10-degree latitudinal bands).")

# Assign regions based on centroids (using period 1 lat/lon for envelope)
# Assuming centroids.csv has 'lat', 'lon' for the first period or average
if (!file.exists(input_centroids)) {
  log_warning("centroids.csv not found. Skipping per-region analysis.")
  write.csv(data.frame(), output_regions, row.names = FALSE)
} else {
  centroids_df <- read.csv(input_centroids, stringsAsFactors = FALSE)
  # Map species to lat band
  # Assuming centroids has 'species' and 'lat' (mean lat)
  if ("lat" %in% names(centroids_df)) {
    merged_data <- merge(clean_data, centroids_df[, c("species", "lat")], by = "species", all.x = TRUE)
    merged_data$lat_band <- cut(merged_data$lat, breaks = seq(-90, 90, by = 10), include.lowest = TRUE)
    merged_data$region_label <- as.character(merged_data$lat_band)
  } else {
    log_warning("Centroids missing 'lat' column. Skipping per-region analysis.")
    merged_data <- clean_data
    merged_data$region_label <- "Unknown"
  }

  region_results <- list()
  unique_regions <- unique(merged_data$region_label)
  unique_regions <- unique_regions[!is.na(unique_regions)]

  log_message(paste("Analyzing", length(unique_regions), "regions."))

  for (region in unique_regions) {
    region_data <- merged_data %>% filter(region_label == region)
    if (nrow(region_data) < 2) {
      log_message(paste("  Region", region, ": Insufficient data (n=", nrow(region_data), "). Skipping."))
      next
    }

    log_message(paste("  Processing region:", region, " (n=", nrow(region_data), ")"))

    # Run WLS for region (simpler, no phylogeny per region usually)
    tryCatch({
      lm_model <- lm(delta_N ~ delta_T, data = region_data)
      summ <- summary(lm_model)
      res <- list(
        region = region,
        n = nrow(region_data),
        slope = coef(lm_model)[2],
        ci_lower = summ$coefficients[2, 1] - 1.96 * summ$coefficients[2, 2],
        ci_upper = coef(lm_model)[2] + 1.96 * summ$coefficients[2, 2],
        r_squared = summ$r.squared,
        p_value = summ$coefficients[2, 4]
      )
      region_results[[region]] <- res
      log_message(paste("    Result: Slope=", round(res$slope, 3), ", p=", format.pval(res$p_value)))
    }, error = function(e) {
      log_warning(paste("    Regression failed for region", region, ":", e$message))
    })
  }

  # Compile and save region results
  if (length(region_results) > 0) {
    region_df <- bind_rows(lapply(region_results, as.data.frame))
    write.csv(region_df, output_regions, row.names = FALSE)
    log_message(paste("Regional results saved to", output_regions))
  } else {
    log_message("No valid region results to save.")
    write.csv(data.frame(), output_regions, row.names = FALSE)
  }
}

log_message("Analysis completed successfully.")