#!/usr/bin/env Rscript
# Task T025: A Priori Power Analysis for Framing Effect Study
# Verifies that N=300 achieves >= 80% power to detect d=0.3 at alpha=0.05

# Load required libraries
if (!require("pwr", quietly = TRUE)) {
  stop("Package 'pwr' is required but not installed. Please install it via renv.")
}

# Load project utilities
# We source the R equivalent of utils.py logic if needed, 
# but primarily we need to load the config for the seed and parameters.
# Since the project uses R, we assume a config.yaml exists at code/config.yaml
# as per T005.

library(yaml)
library(jsonlite)

# Paths
config_path <- file.path("code", "config.yaml")
output_dir <- file.path("results", "processed")
output_file <- file.path(output_dir, "power_analysis_verification.json")

# Ensure output directory exists
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Load Configuration
if (!file.exists(config_path)) {
  stop(paste("Configuration file not found at:", config_path))
}

config <- yaml.load_file(config_path)
seed_val <- if (!is.null(config$seed)) config$seed else 42

# Set seed for reproducibility (though power analysis is deterministic, good practice)
set.seed(seed_val)

# --- Power Analysis Parameters (Fixed by Task Specification) ---
# Effect size (Cohen's d)
d_target <- 0.3
# Significance level (alpha)
alpha_target <- 0.05
# Planned sample size (N)
N_planned <- 300
# Test type: two-sample t-test (between-subjects framing design)
test_type <- "two.sample"

# --- Execute Power Analysis ---
# Calculate power for the planned sample size
# pwr.t.test calculates power given n, d, sig.level, type
# Note: n is the sample size per group. For N=300 total, n=150 per group.
n_per_group <- N_planned / 2

power_result <- pwr.t.test(
  n = n_per_group,
  d = d_target,
  sig.level = alpha_target,
  type = test_type,
  alternative = "two.sided"
)

calculated_power <- power_result$power

# --- Verification Logic ---
threshold <- 0.80
passed <- calculated_power >= threshold

# --- Logging and Halting ---
message(paste("Power Analysis Results:"))
message(paste("  Target Effect Size (d):", d_target))
message(paste("  Planned Total N:", N_planned))
message(paste("  N per Group:", n_per_group))
message(paste("  Alpha:", alpha_target))
message(paste("  Calculated Power:", round(calculated_power, 4)))
message(paste("  Threshold:", threshold))

if (!passed) {
  msg <- paste("CRITICAL WARNING: Calculated power (", 
               round(calculated_power, 4), 
               ") is below the required threshold (", 
               threshold, "). The study may be underpowered.",
               sep = "")
  message(msg)
  # Halt execution as per specification
  stop(msg)
} else {
  message("SUCCESS: Planned sample size N=300 achieves >= 80% power.")
}

# --- Export Results ---
results_list <- list(
  target_effect_size = d_target,
  alpha_level = alpha_target,
  planned_total_n = N_planned,
  n_per_group = n_per_group,
  calculated_power = calculated_power,
  power_threshold = threshold,
  verification_passed = passed,
  seed_used = seed_val
)

# Write to JSON
jsonlite::write_json(
  results_list,
  path = output_file,
  pretty = TRUE,
  auto_unbox = TRUE
)

message(paste("Results saved to:", output_file))

# Explicit exit with success code
quit(status = 0)
