#!/usr/bin/env Rscript
# power_analysis.R
# Task T025: Implement a priori power analysis for niche shift vs regional warming regression.
#
# Requirements (FR-012, SC-007):
# - Conduct a priori power analysis for n >= 30 species.
# - Parameters: alpha = 0.05, power = 0.80.
# - Read effect_size from config.yaml (default to moderate magnitude if missing).
# - Calculate required n to achieve Margin of Error (MoE) <= 0.15 for slope estimate.
# - Report MoE and save results to results/power_analysis_report.csv.

# Load dependencies
if (!requireNamespace("yaml", quietly = TRUE)) {
  stop("Package 'yaml' is required. Please install it via install.packages('yaml').")
}
if (!requireNamespace("pwr", quietly = TRUE)) {
  stop("Package 'pwr' is required. Please install it via install.packages('pwr').")
}

library(yaml)
library(pwr)
library(dplyr)

# Configuration
CONFIG_PATH <- "config.yaml"
OUTPUT_PATH <- "results/power_analysis_report.csv"
TARGET_MOE <- 0.15
DEFAULT_EFFECT_SIZE <- 0.3  # Cohen's f^2 interpretation for moderate effect in regression

# Helper: Load config
load_config <- function(path) {
  if (!file.exists(path)) {
    warning(sprintf("Config file '%s' not found. Using defaults.", path))
    return(list(effect_size = DEFAULT_EFFECT_SIZE))
  }
  config <- yaml.load_file(path)
  return(config)
}

# Helper: Ensure output directory exists
ensure_dir <- function(path) {
  dir_name <- dirname(path)
  if (!dir.exists(dir_name)) {
    dir.create(dir_name, recursive = TRUE)
  }
}

# Main Logic
main <- function() {
  cat("Starting Power Analysis (T025)...\n")
  
  # 1. Load Configuration
  config <- load_config(CONFIG_PATH)
  effect_size <- config$effect_size
  
  if (is.null(effect_size) || is.na(effect_size)) {
    cat(sprintf("Effect size not found in config, using default: %f\n", DEFAULT_EFFECT_SIZE))
    effect_size <- DEFAULT_EFFECT_SIZE
  } else {
    cat(sprintf("Using effect size from config: %f\n", effect_size))
  }
  
  # 2. Define Parameters
  alpha <- 0.05
  desired_power <- 0.80
  min_n_species <- 30
  
  # 3. Calculate Required Sample Size (n) for Target MoE
  # The Margin of Error (MoE) for a regression slope is approx: t_crit * SE_slope.
  # In the context of pwr, we first find the n required to achieve 'desired_power'
  # for a linear regression with 1 predictor (k=1).
  # We assume a simple linear model: y ~ x.
  
  # Calculate n for the given power and effect size
  # pwr.r.test tests correlation, which is equivalent for simple linear regression
  # effect_size here is treated as 'r' (correlation coefficient) if < 1, 
  # or we convert f^2 to r. Assuming input is 'r' for simplicity or f^2.
  # If input is f^2 (Cohen's f^2), r = sqrt(f^2 / (1 + f^2)).
  # We assume the config provides 'r' (correlation) for direct pwr.r.test usage,
  # or a small/moderate effect size typical for ecological slopes.
  # To be robust, if effect_size > 1, treat as f^2, else treat as r.
  
  r_val <- effect_size
  if (effect_size > 1) {
    # Convert f^2 to r
    r_val <- sqrt(effect_size / (1 + effect_size))
  }
  
  cat(sprintf("Calculating sample size for r = %f, power = %f, alpha = %f...\n", r_val, desired_power, alpha))
  
  power_result <- tryCatch({
    pwr.r.test(r = r_val, sig.level = alpha, power = desired_power, alternative = "two.sided")
  }, error = function(e) {
    stop(paste("Power calculation failed:", e$message))
  })
  
  n_required <- ceiling(power_result$n)
  cat(sprintf("Sample size (n) required for power %f: %d\n", desired_power, n_required))
  
  # 4. Calculate Margin of Error (MoE) for the calculated n
  # MoE = t_(1-alpha/2, df=n-2) * SE_slope
  # We approximate SE_slope using the relationship: SE_slope = (SD_y / (SD_x * sqrt(n-1))) * sqrt(1-r^2)
  # However, without raw data SDs, we use the standard error of the slope in standardized units.
  # In standardized units (z-scored), SD_y = 1, SD_x = 1.
  # SE_slope_standardized = sqrt((1 - r^2) / (n - 2))
  # t_crit = qt(1 - alpha/2, df = n - 2)
  # MoE = t_crit * SE_slope_standardized
  
  df <- n_required - 2
  if (df <= 0) {
    stop("Calculated n is too small to compute degrees of freedom for regression.")
  }
  
  t_crit <- qt(1 - alpha / 2, df = df)
  se_slope_std <- sqrt((1 - r_val^2) / df)
  moe <- t_crit * se_slope_std
  
  cat(sprintf("Calculated MoE for n=%d: %f (Target: %f)\n", n_required, moe, TARGET_MOE))
  
  # 5. Determine Final Sample Size Recommendation
  # We need n such that MoE <= TARGET_MOE.
  # If current n gives MoE > TARGET_MOE, we must increase n.
  # Since MoE decreases as n increases, we can iterate or estimate.
  # For simplicity, we report the n for power and the resulting MoE.
  # If MoE > TARGET_MOE, we recommend increasing n until MoE <= TARGET_MOE.
  
  recommended_n <- n_required
  final_moe <- moe
  
  # Iterative check to meet MoE constraint if not met by power calculation
  if (moe > TARGET_MOE) {
    cat(sprintf("MoE (%f) exceeds target (%f). Increasing sample size...\n", moe, TARGET_MOE))
    current_n <- n_required
    while (TRUE) {
      current_n <- current_n + 1
      current_df <- current_n - 2
      current_t <- qt(1 - alpha / 2, df = current_df)
      current_se <- sqrt((1 - r_val^2) / current_df)
      current_moe <- current_t * current_se
      
      if (current_moe <= TARGET_MOE || current_n > 1000) {
        recommended_n <- current_n
        final_moe <- current_moe
        break
      }
    }
    cat(sprintf("New recommended n to meet MoE target: %d (MoE: %f)\n", recommended_n, final_moe))
  }
  
  # Ensure minimum n constraint
  if (recommended_n < min_n_species) {
    cat(sprintf("Recommended n (%d) is below minimum species count (%d). Adjusting.\n", recommended_n, min_n_species))
    recommended_n <- min_n_species
    # Recalculate MoE for this n
    df_final <- recommended_n - 2
    t_final <- qt(1 - alpha / 2, df = df_final)
    se_final <- sqrt((1 - r_val^2) / df_final)
    final_moe <- t_final * se_final
  }
  
  # 6. Prepare Output
  results_df <- data.frame(
    parameter = c("alpha", "power", "effect_size", "min_species", "required_n_power", "required_n_moe", "final_recommended_n", "achieved_moe", "target_moe"),
    value = c(alpha, desired_power, effect_size, min_n_species, n_required, recommended_n, recommended_n, final_moe, TARGET_MOE),
    stringsAsFactors = FALSE
  )
  
  # 7. Save Output
  ensure_dir(OUTPUT_PATH)
  write.csv(results_df, OUTPUT_PATH, row.names = FALSE)
  
  cat(sprintf("Power analysis complete. Results saved to %s\n", OUTPUT_PATH))
  cat(sprintf("Final Recommendation: n = %d species to achieve Power=%f and MoE <= %f\n", recommended_n, desired_power, TARGET_MOE))
}

# Execute
main()
