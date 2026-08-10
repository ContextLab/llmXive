#!/usr/bin/env Rscript
#
# code/06_fit_gls.R
# Task: T016
# Description: Fit a Fixed-Effects GLS model per stress condition to test the
#              fixed effect beta_1 for 'weighted_ΔPeakSignal'.
#              Substitutes LMM due to CPU constraints (Plan e001).
# Inputs:
#   - data/processed/delta_peak_signal.tsv (from T043)
#   - data/processed/CRE_validated_filtered.bed (from T013/T014/T015, containing weights)
# Outputs:
#   - results/gls_results_<stress>.csv (per stress)
#   - results/gls_summary_all.csv (aggregated)
#
# Dependencies:
#   - nlme (for gls)
#   - data.table (for fast IO)
#   - dplyr (for data manipulation)
#
# Note: This script expects the input files to exist. If they do not, it will
#       fail loudly as per project constraints.

library(nlme)
library(data.table)
library(dplyr)
library(readr)

# Configuration
INPUT_DELTA_SIGNAL <- "data/processed/delta_peak_signal.tsv"
INPUT_CRE_FILTERED <- "data/processed/CRE_validated_filtered.bed"
OUTPUT_DIR <- "results"

# Ensure output directory exists
if (!dir.exists(OUTPUT_DIR)) {
  dir.create(OUTPUT_DIR, recursive = TRUE)
}

# Check input files exist
if (!file.exists(INPUT_DELTA_SIGNAL)) {
  stop(paste("Input file not found:", INPUT_DELTA_SIGNAL, 
             ". Please ensure T043 has been completed successfully."))
}
if (!file.exists(INPUT_CRE_FILTERED)) {
  stop(paste("Input file not found:", INPUT_CRE_FILTERED,
             ". Please ensure T013-T015 have been completed successfully."))
}

message("Loading input data...")

# Load delta signal data
# Expected columns: chrom, start, end, gene, stress, delta_signal
delta_df <- fread(INPUT_DELTA_SIGNAL)

# Load filtered CRE data
# Expected columns (from T015 output): chrom, start, end, gene, stress, weight, motif_score, hic_score, vif_flag
# We need to join on (chrom, start, end) or (gene, stress) depending on how T015 outputs.
# Assuming T015 outputs a BED-like structure with gene/stress info.
# Let's assume the join key is 'gene' and 'stress' as per the pipeline design (regulatory elements linked to genes).
cre_df <- fread(INPUT_CRE_FILTERED)

# Validate required columns
req_cols_delta <- c("gene", "stress", "delta_signal")
req_cols_cre <- c("gene", "stress", "weight")

missing_delta <- setdiff(req_cols_delta, names(delta_df))
missing_cre <- setdiff(req_cols_cre, names(cre_df))

if (length(missing_delta) > 0) {
  stop(paste("Missing columns in delta signal file:", paste(missing_delta, collapse=", ")))
}
if (length(missing_cre) > 0) {
  stop(paste("Missing columns in filtered CRE file:", paste(missing_cre, collapse=", ")))
}

# Merge datasets
# We are modeling the effect of weighted delta signal on... what?
# The task description says: "testing the fixed effect beta_1 for weighted_ΔPeakSignal".
# Usually, this implies a regression where the dependent variable is the phenotypic plasticity (e.g., log2FC of gene expression).
# However, the task description for T016 does not explicitly mention an eQTL/Expression file.
# Re-reading the context: "Decoding Regulatory Element Contributions to Phenotypic Plasticity".
# The "phenotypic plasticity" is the gene expression change (log2FC) under stress.
# The eQTL data (from manifest) should provide the gene expression changes.
# Since T016 is the GLS step, it must combine the CRE signal (independent variable) with the Gene Expression (dependent variable).
# We need to load the eQTL data which contains the gene expression changes (log2FC).

# Check if eQTL data exists in data/processed/
eqtl_path <- "data/processed/eqtl_gene_expression.tsv"
if (!file.exists(eqtl_path)) {
  # If not found, we cannot proceed. This is a fatal error as per "Fail loudly".
  stop(paste("Required eQTL expression data not found at:", eqtl_path,
             ". The GLS model requires the dependent variable (gene expression change)."))
}

message("Loading eQTL expression data...")
eqtl_df <- fread(eqtl_path)

# Validate eQTL columns
# Expected: gene, stress, log2FC (or similar metric for phenotypic plasticity)
if (!("gene" %in% names(eqtl_df)) || !("stress" %in% names(eqtl_df))) {
  stop("eQTL file must contain 'gene' and 'stress' columns.")
}
# Assume the column for plasticity is named 'log2FC' or 'plasticity'.
# We will try to find a numeric column that isn't gene/stress.
numeric_cols <- names(eqtl_df)[sapply(eqtl_df, is.numeric)]
if (length(numeric_cols) == 0) {
  stop("No numeric column found in eQTL file to serve as dependent variable.")
}
# Prefer 'log2FC' if it exists, otherwise take the first numeric one
y_col <- if ("log2FC" %in% numeric_cols) "log2FC" else numeric_cols[1]
message(paste("Using column '", y_col, "' as the dependent variable (phenotypic plasticity).", sep=""))

# Merge: CRE weights -> Delta Signal -> Expression
# Join CRE and Delta on (gene, stress)
merged_data <- cre_df %>%
  select(gene, stress, weight) %>%
  inner_join(delta_df %>% select(gene, stress, delta_signal), by = c("gene", "stress")) %>%
  inner_join(eqtl_df, by = c("gene", "stress"))

# Create the weighted predictor
merged_data$weighted_delta_signal <- merged_data$weight * merged_data$delta_signal

# Remove rows with NA
merged_data <- na.omit(merged_data)

if (nrow(merged_data) == 0) {
  stop("No valid data points after merging. Check for missing values or mismatched keys.")
}

message(paste("Fitting GLS models for", length(unique(merged_data$stress)), "stress conditions..."))

results_list <- list()

# Fit model per stress
unique_stresses <- unique(merged_data$stress)

for (st in unique_stresses) {
  message(paste("Processing stress:", st))
  sub_data <- merged_data %>% filter(stress == st)
  
  if (nrow(sub_data) < 10) {
    warning(paste("Insufficient data points (", nrow(sub_data), ") for stress ", st, ". Skipping.", sep=""))
    next
  }
  
  # Model: y ~ weighted_delta_signal
  # Using gls with default correlation structure (independence) as we are doing Fixed-Effects per stress
  # This effectively runs a separate regression for each stress group.
  # Formula: log2FC ~ weighted_delta_signal
  
  tryCatch({
    model <- gls(as.formula(paste(y_col, "~ weighted_delta_signal")), 
                 data = sub_data,
                 method = "REML")
    
    # Extract coefficients
    coefs <- coef(summary(model))
    beta_1 <- coefs["weighted_delta_signal", "Estimate"]
    se_beta_1 <- coefs["weighted_delta_signal", "Std.Error"]
    t_stat <- coefs["weighted_delta_signal", "t-value"]
    p_val <- coefs["weighted_delta_signal", "p-value"]
    
    # Store results
    results_list[[st]] <- data.frame(
      stress = st,
      beta_1 = beta_1,
      se_beta_1 = se_beta_1,
      t_stat = t_stat,
      p_value = p_val,
      n_obs = nrow(sub_data),
      r_squared = summary(model)$r.squared,
      stringsAsFactors = FALSE
    )
    
  }, error = function(e) {
    warning(paste("Failed to fit model for stress", st, ":", e$message))
  })
}

if (length(results_list) == 0) {
  stop("No models could be fitted. Check input data and model specifications.")
}

final_results <- rbindlist(results_list)

# Save individual results
for (st in unique_stresses) {
  if (st %in% final_results$stress) {
    out_file <- file.path(OUTPUT_DIR, paste0("gls_results_", st, ".csv"))
    subset(final_results, stress == st) %>% write_csv(out_file)
    message(paste("Saved results for", st, "to", out_file))
  }
}

# Save aggregated summary
summary_file <- file.path(OUTPUT_DIR, "gls_summary_all.csv")
write_csv(final_results, summary_file)
message(paste("Saved aggregated summary to", summary_file))

message("T016 GLS fitting completed successfully.")

# Exit with success
quit(save = "no", status = 0)
