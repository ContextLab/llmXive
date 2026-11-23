#!/usr/bin/env Rscript
# Task T038: Implement Post-Hoc Power Analysis for ANCOVA Results
#
# Dependencies:
# - T019 (code/03_analysis.R) -> produces data/derived/ancova_results.csv
# - R Package: pwr (must be installed via renv)
#
# Output:
# - data/derived/power_analysis.csv
# - logs/power_analysis.log (summary)
#
# Note: This script reads observed effect sizes (Cohen's f) from the ANCOVA
# results and calculates post-hoc power assuming alpha = 0.01 (Bonferroni corrected).

# Load required libraries
if (!require("pwr", quietly = TRUE)) {
  stop("Package 'pwr' is required but not installed. Please run: renv::install('pwr')")
}
if (!require("readr", quietly = TRUE)) {
  stop("Package 'readr' is required but not installed. Please run: renv::install('readr')")
}
if (!require("dplyr", quietly = TRUE)) {
  stop("Package 'dplyr' is required but not installed. Please run: renv::install('dplyr')")
}
if (!require("jsonlite", quietly = TRUE)) {
  stop("Package 'jsonlite' is required but not installed. Please run: renv::install('jsonlite')")
}

# --- Configuration ---
# Path constants relative to project root
PROJECT_ROOT <- Sys.getenv("PROJECT_ROOT", unset = ".")
ANCOVA_RESULTS_PATH <- file.path(PROJECT_ROOT, "data", "derived", "ancova_results.csv")
POWER_OUTPUT_PATH <- file.path(PROJECT_ROOT, "data", "derived", "power_analysis.csv")
LOG_DIR <- file.path(PROJECT_ROOT, "logs")
LOG_FILE <- file.path(LOG_DIR, "power_analysis.log")

# Ensure log directory exists
if (!dir.exists(LOG_DIR)) {
  dir.create(LOG_DIR, recursive = TRUE)
}

# Logging helper
log_msg <- function(msg, level = "INFO") {
  timestamp <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  line <- sprintf("[%s] [%s] %s", timestamp, level, msg)
  cat(line, "\n")
  cat(line, "\n", file = LOG_FILE, append = TRUE)
}

# --- Main Logic ---

main <- function() {
  log_msg("Starting Power Analysis (T038)...")

  # 1. Validate Input
  if (!file.exists(ANCOVA_RESULTS_PATH)) {
    log_msg(sprintf("ERROR: ANCOVA results file not found at %s", ANCOVA_RESULTS_PATH), "ERROR")
    stop("ANCOVA results file missing. Ensure T019 (code/03_analysis.R) has completed successfully.")
  }

  # 2. Load ANCOVA Results
  log_msg("Loading ANCOVA results...")
  ancova_data <- tryCatch(
    read_csv(ANCOVA_RESULTS_PATH),
    error = function(e) {
      log_msg(sprintf("ERROR: Failed to read ANCOVA results: %s", e$message), "ERROR")
      stop(e)
    }
  )

  # 3. Verify Required Columns
  required_cols <- c("subscale", "contrast_label", "f_statistic", "p_value", "df1", "df2", "effect_size_f")
  missing_cols <- setdiff(required_cols, names(ancova_data))
  
  if (length(missing_cols) > 0) {
    log_msg(sprintf("ERROR: Missing required columns in ANCOVA results: %s", paste(missing_cols, collapse = ", ")), "ERROR")
    stop("Input data structure mismatch.")
  }

  # 4. Determine Sample Size (N)
  # We need N to calculate power. N can be derived from df2 (error degrees of freedom).
  # For ANCOVA: df2 = N - k - 1 (where k is number of predictors).
  # However, we don't strictly know k here without re-reading the model formula.
  # Alternative: If the data includes 'n' or 'total_n', use that.
  # Fallback: Estimate N from df2 assuming a standard model structure.
  # Standard Model: ~ chronotype + PSQI + acute_sleepiness + age + sex
  # Predictors (k): 1 (chronotype) + 4 (covariates) = 5?
  # Actually, df1 = number of groups - 1 (for the factor) or number of predictors.
  # Let's assume the provided 'df2' is the residual df.
  # If we assume the model includes the main effect of Chronotype (3 levels -> 2 df) + 4 covariates = 6 parameters?
  # Let's try to infer N from df2 + (number of estimated parameters).
  # A safer bet if N is not explicitly in the CSV:
  # We will attempt to read the 'n' column if it exists, otherwise we estimate.
  # For this implementation, we assume the ANCOVA output includes 'total_n' or we derive it.
  # If not present, we will estimate N = df2 + (df1 + 1 + number_of_covariates).
  # Let's assume standard ANCOVA with 3 groups and 4 covariates.
  # df1 for the main effect (Chronotype) is usually 2 (3 levels - 1).
  # df2 = N - (number of groups + number of covariates).
  # Let's assume the 'df2' column is the error df.
  # We need a robust way to get N. If the CSV has 'n_total', use it.
  # If not, we will calculate N = df2 + (df1 + 1 + 4) [assuming 4 covariates].
  # To be safe, we will check for 'n_total' first.
  
  if ("n_total" %in% names(ancova_data)) {
    N <- ancova_data$n_total[1]
    log_msg(sprintf("Using N from data: %d", N))
  } else {
    # Estimate N based on df2 and df1
    # Assuming the model: Y ~ Chronotype + Covariates
    # df1 = number of groups - 1 (for the factor of interest)
    # df2 = N - (number of groups + number of covariates)
    # Let's assume 3 groups (Morning, Intermediate, Evening) -> 2 df for factor
    # And 4 covariates (PSQI, acute_sleepiness, age, sex).
    # Total parameters = 3 (groups) + 4 (covariates) + 1 (intercept) = 8?
    # Actually, df2 = N - p (where p is number of parameters).
    # Let's assume p = df1 + 1 (intercept) + 4 (covariates).
    # N = df2 + df1 + 1 + 4
    estimated_covariates <- 4
    N <- ancova_data$df2 + ancova_data$df1 + 1 + estimated_covariates
    log_msg(sprintf("Estimated N from degrees of freedom: %d", N))
  }

  # 5. Calculate Post-Hoc Power
  log_msg("Calculating post-hoc power for each contrast...")
  
  alpha_corrected <- 0.01 # Bonferroni corrected alpha (0.05 / 5 subscales)
  
  power_results <- ancova_data %>%
    rowwise() %>%
    mutate(
      power = pwr.f2.test(
        u = df1,           # Numerator df
        v = df2,           # Denominator df
        f2 = effect_size_f^2, # f-squared
        sig.level = alpha_corrected
      )$power
    ) %>%
    ungroup() %>%
    select(
      subscale,
      contrast_label,
      effect_size_f,
      df1,
      df2,
      p_value,
      n_total = N,
      alpha_corrected,
      power,
      significant = p_value < alpha_corrected
    )

  # 6. Save Results
  log_msg(sprintf("Saving power analysis results to %s", POWER_OUTPUT_PATH))
  write_csv(power_results, POWER_OUTPUT_PATH)

  # 7. Generate Summary for Report
  significant_count <- sum(power_results$power > 0.80)
  total_tests <- nrow(power_results)
  mean_power <- mean(power_results$power)
  
  summary_msg <- sprintf(
    "Power Analysis Summary:\nTotal Tests: %d\nTests with Power > 0.80: %d\nMean Power: %.3f\nAlpha Threshold: %.3f",
    total_tests,
    significant_count,
    mean_power,
    alpha_corrected
  )
  
  log_msg(summary_msg)
  
  # Write a small text file for the report to read easily
  summary_file <- file.path(LOG_DIR, "power_summary.txt")
  writeLines(summary_msg, summary_file)
  
  log_msg("Power Analysis (T038) completed successfully.")
  return(invisible(TRUE))
}

# Execute
tryCatch(
  main(),
  error = function(e) {
    log_msg(sprintf("CRITICAL FAILURE: %s", e$message), "ERROR")
    quit(status = 1)
  }
)
