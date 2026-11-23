#!/usr/bin/env Rscript
# Task: T026 - Confirm N=300 achieves >=80% power for framing effect analysis
# Depends on: T025 (Power Analysis Calculation)
#
# This script loads the power analysis results from T025, verifies that the
# calculated power for N=300 meets the >=80% threshold, and halts execution
# with a critical warning if it does not.

# Load required libraries
if (!require("yaml", quietly = TRUE)) {
  stop("Package 'yaml' is required. Please install it.")
}
if (!require("jsonlite", quietly = TRUE)) {
  stop("Package 'jsonlite' is required. Please install it.")
}
if (!require("pwr", quietly = TRUE)) {
  stop("Package 'pwr' is required. Please install it.")
}

# Source utility functions
# Note: We assume utils.R is in the same directory or accessible via R_LIBS_USER
# If utils.R is in code/, we might need to adjust the path
utils_path <- file.path("code", "utils.R")
if (file.exists(utils_path)) {
  source(utils_path)
}

# Configuration
CONFIG_FILE <- file.path("code", "config.yaml")
POWER_RESULTS_FILE <- file.path("results", "processed", "power_analysis_verification.json")
MIN_POWER_THRESHOLD <- 0.80
TARGET_SAMPLE_SIZE <- 300

# Main execution
main <- function() {
  cat("Starting Power Analysis Verification (T026)...\n")

  # 1. Load configuration for reproducibility
  if (file.exists(CONFIG_FILE)) {
    config <- yaml::read_yaml(CONFIG_FILE)
    if (!is.null(config$seed)) {
      set.seed(as.integer(config$seed))
      cat(sprintf("Random seed set to: %d\n", config$seed))
    }
  } else {
    cat("Warning: config.yaml not found. Using default random seed.\n")
    set.seed(42)
  }

  # 2. Verify T025 output exists
  if (!file.exists(POWER_RESULTS_FILE)) {
    stop(sprintf(
      "Critical Error: Power analysis results file not found at '%s'.\n" %s +
      "Please ensure T025 (code/02_power_analysis.R) has been executed successfully first.",
      POWER_RESULTS_FILE
    ))
  }

  # 3. Load power analysis results
  cat(sprintf("Loading power analysis results from: %s\n", POWER_RESULTS_FILE))
  tryCatch({
    power_results <- jsonlite::fromJSON(POWER_RESULTS_FILE)
  }, error = function(e) {
    stop(sprintf("Failed to parse JSON results: %s", e$message))
  })

  # 4. Extract calculated power
  if (is.null(power_results$calculated_power)) {
    stop("Critical Error: 'calculated_power' field missing in results file.")
  }

  calculated_power <- power_results$calculated_power
  target_effect_size <- power_results$target_effect_size
  sample_size_used <- power_results$sample_size

  cat(sprintf("Target Effect Size (d): %.3f\n", target_effect_size))
  cat(sprintf("Sample Size Used (N): %d\n", sample_size_used))
  cat(sprintf("Calculated Power: %.3f\n", calculated_power))
  cat(sprintf("Minimum Power Threshold: %.2f\n", MIN_POWER_THRESHOLD))

  # 5. Verify power meets threshold
  if (calculated_power >= MIN_POWER_THRESHOLD) {
    cat(sprintf("\nSUCCESS: Calculated power (%.2f) meets the threshold (%.2f).\n",
                calculated_power, MIN_POWER_THRESHOLD))
    cat("Execution can proceed to analysis.\n")
    return(invisible(TRUE))
  } else {
    warning_msg <- sprintf(
      "CRITICAL WARNING: Calculated power (%.2f) is BELOW the threshold (%.2f).\n" %s +
      "The planned sample size (N=%d) is insufficient to detect the target effect size (d=%.3f) with 80%% power.\n" %s +
      "Execution HALTED. Please increase sample size or re-evaluate the effect size assumption.",
      calculated_power, MIN_POWER_THRESHOLD, sample_size_used, target_effect_size
    )
    cat(sprintf("\n%s\n", warning_msg))
    stop("Power analysis verification failed. Halting execution.")
  }
}

# Run main if executed as script
if (!interactive()) {
  main()
}
# End of script