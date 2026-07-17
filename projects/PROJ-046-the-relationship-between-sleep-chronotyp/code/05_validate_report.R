#!/usr/bin/env Rscript
# code/05_validate_report.R
# Validates the generated R-Markdown report for required sections and content
#
# This script ensures that the final analysis report contains all required sections
# as specified in the project requirements (SC-003).

library(readr)
library(stringr)
library(dplyr)

# Constants
REQUIRED_SECTIONS <- c(
  "Descriptive Statistics",
  "Chronotype Classification Summary",
  "Reliability Metrics (Cronbach's Alpha)",
  "ANCOVA Results",
  "Effect Sizes (Cohen's d)",
  "Power Analysis",
  "Sensitivity Analysis",
  "Data Exclusion Summary",
  "Conclusions"
)

REQUIRED_COLUMNS_SENSITIVITY <- c(
  "subscale",
  "alpha_threshold",
  "p_value",
  "significant"
)

MIN_ALPHA_THRESHOLDS <- 3

# Function to read report content
read_report_content <- function(report_path) {
  if (!file.exists(report_path)) {
    stop(paste("Report file not found:", report_path))
  }

  # Read HTML content
  content <- read_lines(report_path, warn = FALSE)
  paste(content, collapse = "\n")
}

# Function to validate report structure
validate_report <- function(report_path) {
  cat("Validating report:", report_path, "\n")

  # Read report content
  content <- read_report_content(report_path)

  # Check for required sections
  missing_sections <- c()
  for (section in REQUIRED_SECTIONS) {
    if (!str_detect(content, str_c("\\b", section, "\\b", ignore_case = TRUE))) {
      missing_sections <- c(missing_sections, section)
    }
  }

  if (length(missing_sections) > 0) {
    cat("ERROR: Missing required sections:\n")
    for (section in missing_sections) {
      cat("  -", section, "\n")
    }
    return(FALSE)
  }

  cat("✓ All required sections present\n")

  # Validate sensitivity analysis table
  if (file.exists("data/derived/sensitivity_sweep.csv")) {
    sensitivity_data <- read_csv("data/derived/sensitivity_sweep.csv", show_col_types = FALSE)

    # Check required columns
    missing_cols <- setdiff(REQUIRED_COLUMNS_SENSITIVITY, names(sensitivity_data))
    if (length(missing_cols) > 0) {
      cat("ERROR: Sensitivity table missing columns:\n")
      for (col in missing_cols) {
        cat("  -", col, "\n")
      }
      return(FALSE)
    }

    # Check minimum alpha thresholds
    unique_thresholds <- unique(sensitivity_data$alpha_threshold)
    if (length(unique_thresholds) < MIN_ALPHA_THRESHOLDS) {
      cat("ERROR: Sensitivity table has", length(unique_thresholds),
          "alpha thresholds, but requires at least", MIN_ALPHA_THRESHOLDS, "\n")
      return(FALSE)
    }

    cat("✓ Sensitivity analysis table valid\n")
    cat("  - Columns:", paste(REQUIRED_COLUMNS_SENSITIVITY, collapse = ", "), "\n")
    cat("  - Alpha thresholds:", length(unique_thresholds), "\n")
  } else {
    cat("WARNING: Sensitivity sweep file not found (data/derived/sensitivity_sweep.csv)\n")
  }

  # Validate reliability metrics
  if (file.exists("data/derived/reliability_metrics.csv")) {
    reliability_data <- read_csv("data/derived/reliability_metrics.csv", show_col_types = FALSE)

    required_rel_cols <- c("subscale", "cronbach_alpha", "n_items")
    missing_rel_cols <- setdiff(required_rel_cols, names(reliability_data))

    if (length(missing_rel_cols) > 0) {
      cat("ERROR: Reliability metrics missing columns:\n")
      for (col in missing_rel_cols) {
        cat("  -", col, "\n")
      }
      return(FALSE)
    }

    # Check for valid alpha values
    invalid_alphas <- sum(reliability_data$cronbach_alpha < 0 | reliability_data$cronbach_alpha > 1)
    if (invalid_alphas > 0) {
      cat("ERROR: Invalid Cronbach's alpha values found (must be between 0 and 1)\n")
      return(FALSE)
    }

    cat("✓ Reliability metrics valid\n")
  } else {
    cat("WARNING: Reliability metrics file not found (data/derived/reliability_metrics.csv)\n")
  }

  # Validate ANCOVA results
  if (file.exists("data/derived/ancova_results.csv")) {
    ancova_data <- read_csv("data/derived/ancova_results.csv", show_col_types = FALSE)

    required_ancova_cols <- c("subscale", "chronotype_contrast", "p_value", "p_value_corrected")
    missing_ancova_cols <- setdiff(required_ancova_cols, names(ancova_data))

    if (length(missing_ancova_cols) > 0) {
      cat("ERROR: ANCOVA results missing columns:\n")
      for (col in missing_ancova_cols) {
        cat("  -", col, "\n")
      }
      return(FALSE)
    }

    cat("✓ ANCOVA results valid\n")
  } else {
    cat("WARNING: ANCOVA results file not found (data/derived/ancova_results.csv)\n")
  }

  # Validate effect sizes
  if (file.exists("data/derived/effect_sizes.csv")) {
    effect_data <- read_csv("data/derived/effect_sizes.csv", show_col_types = FALSE)

    required_effect_cols <- c("subscale", "contrast", "cohen_d", "ci_lower", "ci_upper")
    missing_effect_cols <- setdiff(required_effect_cols, names(effect_data))

    if (length(missing_effect_cols) > 0) {
      cat("ERROR: Effect sizes missing columns:\n")
      for (col in missing_effect_cols) {
        cat("  -", col, "\n")
      }
      return(FALSE)
    }

    cat("✓ Effect sizes valid\n")
  } else {
    cat("WARNING: Effect sizes file not found (data/derived/effect_sizes.csv)\n")
  }

  cat("\n✓ Report validation PASSED\n")
  return(TRUE)
}

# Main execution
main <- function() {
  args <- commandArgs(trailingOnly = TRUE)

  # Default report path
  report_path <- "reports/chronotype_moral_analysis.html"

  # Allow override via command line
  if (length(args) >= 1) {
    report_path <- args[1]
  }

  # Validate report
  is_valid <- validate_report(report_path)

  # Exit with appropriate code
  if (!is_valid) {
    cat("\n✗ Report validation FAILED\n")
    quit(status = 1)
  }

  cat("\n✓ All validations passed successfully\n")
  quit(status = 0)
}

# Run main if executed directly
if (!interactive()) {
  main()
}