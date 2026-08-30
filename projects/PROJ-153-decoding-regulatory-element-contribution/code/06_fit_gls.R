#!/usr/bin/env Rscript
# code/06_fit_gls.R
# Implements Fixed-Effects GLS model for CRE contribution analysis
# Performs Likelihood-Ratio Test (LRT) and Benjamini-Hochberg FDR correction
# Enforces q <= 0.05 cutoff for downstream consumption by T018

library(nlme)
library(dplyr)
library(tidyr)
library(readr)
library(purrr)
library(tools)

# Configuration
ARGS <- commandArgs(trailingOnly = TRUE)
if (length(ARGS) < 2) {
  stop("Usage: Rscript 06_fit_gls.R <input_delta_signal.tsv> <input_merged_cre.bed> <output_gls_results.tsv> <output_fdr_filtered.tsv>")
}

INPUT_DELTA <- ARGS[1]
INPUT_MERGED <- ARGS[2]
OUTPUT_GLS <- ARGS[3]
OUTPUT_FDR <- ARGS[4]

# Ensure output directories exist
dir.create(dirname(OUTPUT_GLS), showWarnings = FALSE, recursive = TRUE)
dir.create(dirname(OUTPUT_FDR), showWarnings = FALSE, recursive = TRUE)

# Logging setup
log_file <- file.path(dirname(OUTPUT_GLS), "06_fit_gls.log")
sink(log_file, type = "message")
cat("Starting GLS fitting and FDR correction at", Sys.time(), "\n")

# Load Data
cat("Loading delta signal data from:", INPUT_DELTA, "\n")
delta_df <- read_tsv(INPUT_DELTA, show_col_types = FALSE)

cat("Loading merged CRE data from:", INPUT_MERGED, "\n")
merged_df <- read_tsv(INPUT_MERGED, show_col_types = FALSE)

# Validate columns
required_delta_cols <- c("cre_id", "stress_condition", "weighted_delta_signal")
required_merged_cols <- c("cre_id", "tf", "start", "end", "strand", "log2fc", "beta1", "pvalue", "qvalue")

missing_delta <- setdiff(required_delta_cols, names(delta_df))
missing_merged <- setdiff(required_merged_cols, names(merged_df))

if (length(missing_delta) > 0) {
  stop(paste("Missing columns in delta signal file:", paste(missing_delta, collapse = ", ")))
}
if (length(missing_merged) > 0) {
  stop(paste("Missing columns in merged CRE file:", paste(missing_merged, collapse = ", ")))
}

# Merge datasets
cat("Merging datasets on cre_id...\n")
model_data <- inner_join(merged_df, delta_df, by = "cre_id")

if (nrow(model_data) == 0) {
  stop("No overlapping CREs found between merged CRE file and delta signal file.")
}

# Clean data for modeling
model_data <- model_data %>%
  filter(!is.na(weighted_delta_signal)) %>%
  mutate(
    stress_condition = as.factor(stress_condition),
    log2fc = as.numeric(log2fc)
  )

# Fit GLS models per stress condition
# Model: log2fc ~ weighted_delta_signal + (TF fixed effects if needed, but task specifies Fixed-Effects GLS)
# We will fit a model per stress condition to allow stress-specific beta1
# Structure: log2fc ~ weighted_delta_signal + tf (as fixed effect)

results_list <- list()

stresses <- unique(model_data$stress_condition)
cat("Processing", length(stresses), "stress conditions.\n")

for (stress in stresses) {
  cat("Processing stress:", stress, "\n")
  subset_data <- model_data %>% filter(stress_condition == stress)
  
  if (nrow(subset_data) < 3) {
    warning(paste("Insufficient data for stress:", stress, "- skipping."))
    next
  }

  # Full model: log2fc ~ weighted_delta_signal + tf
  # Reduced model (for LRT): log2fc ~ tf (testing if weighted_delta_signal adds value)
  # Note: Using 'tf' as a fixed effect proxy for background variation
  
  tryCatch({
    # Fit Full Model
    full_model <- gls(log2fc ~ weighted_delta_signal + tf, 
                      data = subset_data, 
                      method = "REML")
    
    # Fit Reduced Model (Null hypothesis: beta1 = 0)
    reduced_model <- gls(log2fc ~ tf, 
                         data = subset_data, 
                         method = "REML")
    
    # Likelihood Ratio Test
    lrt_result <- anova(full_model, reduced_model)
    lrt_pval <- lrt_result$`p-value`[2]
    
    # Extract coefficients from Full Model
    coef_table <- coef(full_model)
    beta1_val <- coef_table["weighted_delta_signal"]
    se_beta1 <- summary(full_model)$tTable["weighted_delta_signal", "Std.Error"]
    t_stat <- beta1_val / se_beta1
    p_val_beta1 <- 2 * pt(-abs(t_stat), df = full_model$dims$N - length(coef_table))
    
    # Store results
    results_list[[stress]] <- data.frame(
      stress_condition = stress,
      cre_id = NA, # Aggregated per stress for now, or we could do per-cre if model was different
      beta1 = beta1_val,
      se_beta1 = se_beta1,
      p_value = p_val_beta1,
      lrt_p_value = lrt_pval,
      model_status = "success"
    )
    
  }, error = function(e) {
    cat("Error fitting model for", stress, ":", e$message, "\n")
    results_list[[stress]] <- data.frame(
      stress_condition = stress,
      cre_id = NA,
      beta1 = NA,
      se_beta1 = NA,
      p_value = NA,
      lrt_p_value = NA,
      model_status = "failed"
    )
  })
}

# Combine results
if (length(results_list) > 0) {
  all_results <- bind_rows(results_list)
} else {
  stop("No models were successfully fitted.")
}

# Filter out failed models for FDR calculation
valid_results <- all_results %>% filter(model_status == "success")

if (nrow(valid_results) == 0) {
  stop("No valid model results to correct for FDR.")
}

# Benjamini-Hochberg FDR Correction
cat("Applying Benjamini-Hochberg FDR correction to p-values.\n")
valid_results <- valid_results %>%
  mutate(q_value = p.adjust(p_value, method = "BH"))

# Write GLS Results (All valid models)
write_tsv(all_results, OUTPUT_GLS)
cat("GLS results written to:", OUTPUT_GLS, "\n")

# Enforce q <= 0.05 cutoff
significant_results <- valid_results %>%
  filter(q_value <= 0.05)

# Write FDR Filtered Results for T018
write_tsv(significant_results, OUTPUT_FDR)
cat("FDR filtered results (q <= 0.05) written to:", OUTPUT_FDR, "\n")
cat("Number of significant CREs:", nrow(significant_results), "\n")

sink()
cat("GLS fitting and FDR correction completed successfully.\n")
