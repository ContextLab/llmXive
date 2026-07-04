#!/usr/bin/env Rscript
# code/04_export.R
# Export results for all user stories to intermediate JSON files.
# Specifically implements T023: Save US2 logistic regression results.

# Load dependencies
library(jsonlite)
library(dplyr)

# Load configuration for paths and seed
config_path <- file.path("code", "config.yaml")
if (!file.exists(config_path)) {
  stop("Configuration file code/config.yaml not found.")
}
config <- yaml::read_yaml(config_path)

# Define output directories
intermediate_dir <- file.path("results", "intermediate")
if (!dir.exists(intermediate_dir)) {
  dir.create(intermediate_dir, recursive = TRUE)
}

# --- T023: Export US2 Logistic Regression Results ---
# Dependencies: T021 (Odds Ratios), T022 (Interaction Test)
# The analysis script (03_analysis.R) is expected to have populated
# a global environment variable or a saved RData file with the model object.
# We assume the model object 'us2_glm_model' exists or is loaded from a standard location.

# Attempt to load the model object if it was saved by 03_analysis.R
model_path <- file.path("results", "intermediate", "us2_model.RData")
if (file.exists(model_path)) {
  load(model_path)
} else {
  # Fallback: Try to load from a generic analysis results file if specific model file missing
  # This handles cases where the analysis script saved a summary list instead of the raw model
  analysis_results_path <- file.path("results", "intermediate", "us2_analysis_summary.RDS")
  if (file.exists(analysis_results_path)) {
    us2_results_list <- readRDS(analysis_results_path)
  } else {
    stop("US2 Analysis results not found. Ensure code/03_analysis.R has run successfully and saved results.")
  }
}

# If we loaded the raw model object, extract metrics
if (exists("us2_glm_model")) {
  summary_model <- summary(us2_glm_model)
  coef_table <- coef(summary_model)
  
  # Extract framing_condition coefficient (assuming factor levels are set correctly)
  # The coefficient name usually looks like "framing_conditionharm" or similar
  framing_coef_name <- grep("framing_condition", rownames(coef_table), value = TRUE)
  
  if (length(framing_coef_name) == 0) {
    stop("Could not find framing_condition coefficient in model summary.")
  }
  
  # Handle if there are multiple levels (e.g., interaction terms)
  # We specifically want the main effect of the framing condition
  main_effect_row <- coef_table[framing_coef_name[1], ]
  
  # Calculate Odds Ratio
  odds_ratio <- exp(main_effect_row["Estimate"])
  p_value <- main_effect_row["Pr(>|z|)"]
  std_error <- main_effect_row["Std. Error"]
  
  # Check for interaction term if present in the model (T022 requirement)
  interaction_row <- NULL
  interaction_p <- NA
  if (nrow(coef_table) > 3) { # Assuming Intercept + Framing + Domain + Interaction
     # Heuristic: find row with both terms in name
     interaction_candidates <- grep("framing_condition.*content_domain|content_domain.*framing_condition", rownames(coef_table), value = TRUE)
     if (length(interaction_candidates) > 0) {
       interaction_row <- coef_table[interaction_candidates[1], ]
       interaction_p <- interaction_row["Pr(>|z|)"]
     }
  }

  us2_export_data <- list(
    model_type = "logistic_regression",
    formula = as.character(formula(us2_glm_model)),
    n_observations = nrow(model.frame(us2_glm_model)),
    framing_effect = list(
      coefficient = main_effect_row["Estimate"],
      odds_ratio = odds_ratio,
      std_error = std_error,
      z_value = main_effect_row["z value"],
      p_value = p_value
    ),
    interaction_effect = if (!is.null(interaction_row)) list(
      coefficient = interaction_row["Estimate"],
      p_value = interaction_p
    ) else NULL
  )
} else if (exists("us2_results_list")) {
  # If we loaded a pre-computed list
  us2_export_data <- us2_results_list
} else {
  stop("No valid US2 results found in environment or files.")
}

# Write to JSON
output_path <- file.path(intermediate_dir, "us2_results.json")
write_json(us2_export_data, output_path, pretty = TRUE, auto_unbox = TRUE)

cat(sprintf("Successfully exported US2 results to %s\n", output_path))

# --- T018 (US1) & T027 (US3) placeholders ---
# Note: T018 and T027 are handled in their respective analysis/export steps 
# or aggregated in T033. This file focuses on T023 as requested.
# However, to ensure the script is robust if run standalone for US2:
# If US1 or US3 files are missing, we do not fail the whole script, 
# just log a message.

if (!file.exists(file.path(intermediate_dir, "us1_results.json"))) {
  warning("US1 results file not found. T018 may not have run yet.")
}
if (!file.exists(file.path(intermediate_dir, "us3_results.json"))) {
  warning("US3 results file not found. T027 may not have run yet.")
}

# Final aggregation step (T033) is a separate task.
# This script strictly implements T023.
