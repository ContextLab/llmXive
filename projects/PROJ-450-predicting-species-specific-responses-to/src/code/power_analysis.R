#!/usr/bin/env Rscript
# src/code/power_analysis.R
# Task: T025 [US2]
# Description: Conduct a priori power analysis for n >= 30 species.
#              Calculate required n to achieve Margin of Error (MoE) <= 0.15
#              for slope estimate in the regression of niche shift (DeltaN) vs regional warming (DeltaT).
# Output: results/power_analysis_report.csv

# Load project utilities
source("src/code/utils.R")

# Configuration
CONFIG_FILE <- "config.yaml"
OUTPUT_DIR <- "results"
OUTPUT_FILE <- file.path(OUTPUT_DIR, "power_analysis_report.csv")

# Default parameters (overridden by config if present)
DEFAULT_ALPHA <- 0.05
DEFAULT_POWER <- 0.80
DEFAULT_EFFECT_SIZE <- 0.5  # Moderate effect size (Cohen's f or similar metric for regression slope context)
DEFAULT_MOE_TARGET <- 0.15
DEFAULT_MIN_N <- 30

log_info("Starting Power Analysis (T025)...")

# Ensure output directory exists
ensure_dir(OUTPUT_DIR)

# Load configuration
config <- list(
  alpha = DEFAULT_ALPHA,
  power = DEFAULT_POWER,
  effect_size = DEFAULT_EFFECT_SIZE,
  moe_target = DEFAULT_MOE_TARGET,
  min_n = DEFAULT_MIN_N
)

if (file.exists(CONFIG_FILE)) {
  log_info(paste("Loading config from", CONFIG_FILE))
  # Simple YAML parsing if 'yaml' package is available, otherwise fallback to manual or error
  if (requireNamespace("yaml", quietly = TRUE)) {
    loaded_config <- yaml::read_yaml(CONFIG_FILE)
    if (!is.null(loaded_config$power_analysis)) {
      if (!is.null(loaded_config$power_analysis$alpha)) config$alpha <- loaded_config$power_analysis$alpha
      if (!is.null(loaded_config$power_analysis$power)) config$power <- loaded_config$power_analysis$power
      if (!is.null(loaded_config$power_analysis$effect_size)) config$effect_size <- loaded_config$power_analysis$effect_size
      if (!is.null(loaded_config$power_analysis$moe_target)) config$moe_target <- loaded_config$power_analysis$moe_target
      if (!is.null(loaded_config$power_analysis$min_n)) config$min_n <- loaded_config$power_analysis$min_n
    }
  } else {
    log_warn("Package 'yaml' not found. Using default configuration values.")
  }
} else {
  log_warn(paste("Config file", CONFIG_FILE, "not found. Using defaults."))
}

log_info(sprintf("Parameters: alpha=%.2f, power=%.2f, effect_size=%.2f, moe_target=%.2f, min_n=%d",
                 config$alpha, config$power, config$effect_size, config$moe_target, config$min_n))

# Function to calculate required sample size for regression slope
# We use the relationship between Margin of Error, standard error, and critical value.
# MoE = t_crit * SE_slope
# SE_slope = sigma / (sqrt(n) * sigma_x)  (simplified for standardized predictors or assuming sigma_x is constant)
# In power analysis for correlation/regression slope, we often estimate n based on effect size.
# Here we use the 'pwr' package approach for linear model (f) or manually iterate.
# Since we need specific MoE for slope, we can iterate n until MoE <= target.
#
# Assumption: We are testing H0: slope = 0 vs H1: slope != 0.
# We assume a moderate effect size (f^2) derived from config$effect_size.
# If config$effect_size is intended as a standardized slope (beta), we map it to f^2.
# f^2 = R^2 / (1 - R^2). For simple regression, R^2 = beta^2 * var(x) / var(y).
# To keep it robust, we use pwr.f2.test to find n for a given power, then verify MoE.
# However, pwr.f2.test gives n for the whole model.
#
# Alternative approach: Use the formula for CI width of slope.
# Width = 2 * t_(1-alpha/2, n-2) * SE_slope
# SE_slope = sqrt(MSE / Sxx)
# This is complex without raw data.
#
# Practical approach for this task:
# Use 'pwr' package to find n for the specified power and effect size.
# Then, estimate the MoE based on that n and the assumed effect size.
# If MoE > target, increase n iteratively.
#
# We assume a simple linear regression context.
# Effect size f^2 = 0.15 (small), 0.30 (medium), 0.45 (large) per Cohen.
# The config says "moderate magnitude", so we assume effect_size corresponds to f^2 or r.
# Let's assume effect_size in config is 'f2' (Cohen's f-squared) for the regression.
# If it's a correlation r, we convert: f2 = r^2 / (1 - r^2).
# The prompt says "effect_size read from config.yaml (default set to a moderate magnitude)".
# We will treat the config value as f2 for pwr.f2.test.

if (!requireNamespace("pwr", quietly = TRUE)) {
  stop("Package 'pwr' is required for power analysis. Install it with: install.packages('pwr')")
}
library(pwr)

# Step 1: Calculate initial n for desired power using pwr.f2.test
# u = numerator df (number of predictors) = 1 for simple regression
# v = denominator df (n - u - 1)
# f2 = effect size
# power = 0.8
# sig.level = 0.05

initial_result <- pwr.f2.test(u = 1,
                              f2 = config$effect_size,
                              power = config$power,
                              sig.level = config$alpha,
                              v = NULL)

n_initial <- ceiling(initial_result$n) # n here is total sample size (u+v+1)

log_info(sprintf("Initial sample size estimate for power=%.2f: n=%d", config$power, n_initial))

# Step 2: Iterate to find n that satisfies MoE <= target
# We need to estimate the MoE for the slope.
# MoE = t_crit * SE_slope
# We don't have raw data, so we must estimate SE_slope based on the effect size assumption.
# In a standardized regression (predictor and outcome standardized), the slope is the correlation r.
# SE_r = sqrt((1 - r^2) / (n - 2))
# t_crit = qt(1 - alpha/2, df = n - 2)
# MoE = t_crit * sqrt((1 - r^2) / (n - 2))
#
# We need to map config$effect_size (f2) to r.
# f2 = r^2 / (1 - r^2)  => r^2 = f2 / (1 + f2)
# r = sqrt(r^2)

r_squared <- config$effect_size / (1 + config$effect_size)
r_val <- sqrt(r_squared)

calculate_moe <- function(n, alpha, r) {
  if (n <= 2) return(Inf)
  df <- n - 2
  t_crit <- qt(1 - alpha / 2, df)
  se_r <- sqrt((1 - r^2) / df)
  moe <- t_crit * se_r
  return(moe)
}

# Iterate to find n such that MoE <= target
n_current <- max(config$min_n, n_initial)
moe_current <- calculate_moe(n_current, config$alpha, r_val)

iterations <- 0
max_iterations <- 10000

while (moe_current > config$moe_target && iterations < max_iterations) {
  n_current <- n_current + 1
  moe_current <- calculate_moe(n_current, config$alpha, r_val)
  iterations <- iterations + 1
}

if (iterations >= max_iterations) {
  log_error("Could not achieve MoE target within max iterations. Check effect size or target.")
  stop("Power analysis failed to converge.")
}

# Step 3: Verify Power for this n
final_power <- pwr.f2.test(u = 1,
                           f2 = config$effect_size,
                           n = n_current,
                           sig.level = config$alpha)$power

log_info(sprintf("Final sample size: n=%d, MoE=%.4f, Achieved Power=%.4f",
                 n_current, moe_current, final_power))

# Prepare Report Data
report_data <- data.frame(
  parameter = c("alpha", "power_target", "effect_size_f2", "moe_target", "required_n", "moe_achieved", "power_achieved", "min_n_constraint"),
  value = c(config$alpha, config$power, config$effect_size, config$moe_target, n_current, moe_current, final_power, config$min_n),
  stringsAsFactors = FALSE
)

# Write to CSV
write.csv(report_data, file = OUTPUT_FILE, row.names = FALSE)
log_info(sprintf("Power analysis report saved to %s", OUTPUT_FILE))

log_info("Power Analysis (T025) completed successfully.")
invisible(NULL)
