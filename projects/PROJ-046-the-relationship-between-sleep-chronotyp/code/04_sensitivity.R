#!/usr/bin/env Rscript
# T027: Sensitivity Analysis Sweep
# Re-runs ANCOVA models for different alpha thresholds to generate sensitivity table.

library(tidyverse)
library(lme4)
library(car)
library(effectsize)
library(data.table)

# Configuration
DATA_PATH <- "data/derived/classified_data.csv"
SENSITIVITY_OUTPUT <- "data/derived/sensitivity_sweep.csv"
ALPHA_THRESHOLDS <- c(0.01, 0.0125, 0.015)

# Subscales to analyze (assuming standard MFQ structure)
# These should match the columns in classified_data.csv derived from T012
SUBSCALES <- c("MFQ_Harm", "MFQ_Fairness", "MFQ_Loyalty", "MFQ_Authority", "MFQ_Purity")

# Check dependencies
if (!file.exists(DATA_PATH)) {
  stop("Required input data not found at: ", DATA_PATH)
}

cat("Loading classified data...\n")
data <- read_csv(DATA_PATH)

# Verify required columns
required_cols <- c("chronotype", "PSQI", "acute_sleepiness", "age", "sex")
missing_cols <- setdiff(required_cols, names(data))
if (length(missing_cols) > 0) {
  stop("Missing required columns for ANCOVA: ", paste(missing_cols, collapse = ", "))
}

cat("Running sensitivity sweep for alpha thresholds:", paste(ALPHA_THRESHOLDS, collapse = ", "), "\n")

results_list <- list()

for (subscale in SUBSCALES) {
  if (!(subscale %in% names(data))) {
    warning("Subscale ", subscale, " not found in data. Skipping.")
    next
  }

  cat("Processing subscale:", subscale, "\n")
  
  # Prepare formula
  formula_str <- as.formula(paste(subscale, "~ chronotype + PSQI + acute_sleepiness + age + sex"))
  
  # Fit model once (re-fitting for each threshold is statistically redundant for p-values, 
  # but we re-run the significance check logic per threshold as requested)
  model <- tryCatch({
    lm(formula_str, data = data)
  }, error = function(e) {
    warning("Failed to fit model for ", subscale, ": ", e$message)
    return(NULL)
  })

  if (is.null(model)) next

  # Extract p-value for the main effect of interest (chronotype)
  # We assume 'chronotype' is a factor. We look at the F-test for the term.
  anova_res <- anova(model)
  
  # Find the row for 'chronotype'
  chronotype_row <- which(rownames(anova_res) == "chronotype")
  
  if (length(chronotype_row) == 0) {
    warning("chronotype term not found in ANOVA table for ", subscale)
    next
  }

  p_val <- anova_res[chronotype_row, "Pr(>F)"]

  # Generate results for each threshold
  for (alpha in ALPHA_THRESHOLDS) {
    sig_status <- ifelse(p_val < alpha, TRUE, FALSE)
    
    results_list[[length(results_list) + 1]] <- data.frame(
      subscale = subscale,
      alpha_threshold = alpha,
      p_value = p_val,
      significant = sig_status
    )
  }
}

if (length(results_list) == 0) {
  stop("No results generated. Check subscale names and data.")
}

final_results <- bind_rows(results_list)

# Sort for readability
final_results <- final_results %>%
  arrange(subscale, alpha_threshold)

# Save output
write_csv(final_results, SENSITIVITY_OUTPUT)

cat("Sensitivity analysis complete. Results saved to:", SENSITIVITY_OUTPUT, "\n")
print(final_results)
