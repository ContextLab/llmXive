#!/usr/bin/env Rscript
# 03_analysis.R
# Purpose: Fit mixed-effects models (US1) and logistic regression models (US2)
#          including interaction tests for framing and content domain.

# Load required libraries
suppressPackageStartupMessages({
  library(lme4)
  library(lmerTest)
  library(dplyr)
  library(tidyr)
  library(jsonlite)
  library(readr)
})

# Source utilities from Python side via reticulate or standard R utilities
# Since the project uses R for analysis, we assume standard R utils or
# a bridge. For this task, we implement the logic directly in R.
# Note: The project has code/utils.py, but R scripts typically source R helpers.
# We will implement the necessary helper logic inline or assume standard paths.

# Configuration
args <- commandArgs(trailingOnly = TRUE)
# Expected args: --data <path_to_processed_data> --output <path_to_output_json>
# If not provided, use defaults based on project structure
data_path <- if (length(args) >= 2) args[2] else "data/processed/synthetic_severity_data.csv"
output_path <- if (length(args) >= 4) args[4] else "results/intermediate/us2_results.json"

# Ensure output directory exists
output_dir <- dirname(output_path)
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Load Data
if (!file.exists(data_path)) {
  stop(paste("Error: Data file not found at", data_path))
}

cat("Loading data from:", data_path, "\n")
df <- read_csv(data_path)

# Validate required columns
required_cols <- c("severity_rating", "framing_condition", "content_domain", 
                   "sharing_intention", "stimulus_id", "participant_id")
missing_cols <- setdiff(required_cols, names(df))
if (length(missing_cols) > 0) {
  stop(paste("Error: Missing required columns:", paste(missing_cols, collapse = ", ")))
}

# Ensure factors are correctly typed
df$framing_condition <- factor(df$framing_condition, levels = c("harm", "fact"))
df$content_domain <- factor(df$content_domain)
df$stimulus_id <- factor(df$stimulus_id)
df$sharing_intention <- as.integer(df$sharing_intention)

cat("Data loaded successfully. N =", nrow(df), "\n")

# ----------------------------------------------------------------------
# US2 Analysis: Logistic Regression for Sharing Intention
# ----------------------------------------------------------------------
# Task T020: Fit logistic regression model predicting sharing_intention
#            from framing_condition and content_domain.
# Task T021: Calculate odds ratios and p-values.
# Task T022: Test and report the interaction coefficient.

cat("\n--- Starting US2 Analysis ---\n")

# Fit model with interaction
# Formula: sharing_intention ~ framing_condition * content_domain
model_us2 <- glm(
  sharing_intention ~ framing_condition * content_domain,
  data = df,
  family = binomial(link = "logit")
)

# Extract summary
summary_model <- summary(model_us2)

# Extract coefficients table
coef_table <- coef(summary_model)

# Calculate Odds Ratios and Confidence Intervals
# confint.default uses Wald approximation; confint uses profile (slower but better)
# For speed on CI, we use Wald for OR and CI unless specified otherwise.
# Given constraints, we'll use confint.default for speed.
conf_int <- confint.default(model_us2)

# Create a results dataframe
results_list <- list()

# Iterate over coefficients to build structured output
# We specifically look for the interaction term
interaction_term <- "framing_conditionfact:content_domain" 
# Note: The exact name depends on factor levels. We search for the interaction.

interaction_found <- FALSE
interaction_results <- list()

for (term in rownames(coef_table)) {
  estimate <- coef_table[term, "Estimate"]
  std_err <- coef_table[term, "Std. Error"]
  z_val <- coef_table[term, "z value"]
  p_val <- coef_table[term, "Pr(>|z|)"]
  
  # Calculate Odds Ratio
  or_val <- exp(estimate)
  or_ci_lower <- exp(conf_int[term, 1])
  or_ci_upper <- exp(conf_int[term, 2])

  term_result <- list(
    term = term,
    estimate = estimate,
    std_error = std_err,
    z_value = z_val,
    p_value = p_val,
    odds_ratio = or_val,
    ci_lower = or_ci_lower,
    ci_upper = or_ci_upper
  )

  results_list[[term]] <- term_result

  # Check if this is the interaction term
  if (grepl("framing_condition", term) && grepl("content_domain", term) && grepl(":", term)) {
    interaction_found <- TRUE
    interaction_results <- term_result
  }
}

if (!interaction_found) {
  warning("Interaction term not found in model output. Check factor levels.")
}

# Compile final US2 results structure
us2_results <- list(
  model_type = "Logistic Regression (GLM)",
  formula = "sharing_intention ~ framing_condition * content_domain",
  sample_size = nrow(df),
  main_effects = list(
    framing_condition = results_list[["framing_conditionfact"]], # Assuming 'fact' is the non-reference level
    content_domain = results_list[names(results_list)[grepl("content_domain", names(results_list)) & !grepl(":", names(results_list))]]
  ),
  interaction = interaction_results,
  convergence = model_us2$converged,
  deviance = model_us2$deviance,
  null_deviance = model_us2$null.deviance
)

# Save to JSON
cat("Saving results to:", output_path, "\n")
write_json(us2_results, output_path, pretty = TRUE, auto_unbox = TRUE)

cat("\n--- US2 Analysis Complete ---\n")
cat("Interaction term reported:\n")
if (interaction_found) {
  print(interaction_results)
} else {
  cat("No interaction term detected.\n")
}

# Exit successfully
quit(status = 0)