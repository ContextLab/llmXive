#!/usr/bin/env Rscript
#
# run_r_script.R
# Performs Differential Expression (DESeq2) on the provided count matrix and sample metadata.
#
# Usage:
#   Rscript run_r_script.R <count_matrix_path> <metadata_path> <output_dir>
#
# Inputs:
#   <count_matrix_path>: Path to CSV/TSV with genes as rows, samples as columns.
#   <metadata_path>: Path to CSV/TSV with sample columns including 'condition' and optional 'batch'.
#   <output_dir>: Directory where results will be written.
#
# Outputs:
#   - <output_dir>/results.csv: DESeq2 results table (log2FC, pvalue, padj, etc.)
#   - <output_dir>/dispersion_params.csv: Fixed dispersion parameters for permutation (US2)
#   - <output_dir>/model_info.json: Metadata about the run (formula, coefficients)
#

# Suppress package startup messages for cleaner logs
suppressPackageStartupMessages({
  library(DESeq2)
  library(dplyr)
  library(jsonlite)
  library(readr)
})

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 3) {
  stop("Usage: Rscript run_r_script.R <count_matrix_path> <metadata_path> <output_dir>")
}

count_file <- args[1]
meta_file <- args[2]
output_dir <- args[3]

# Ensure output directory exists
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

message("Loading count matrix from: ", count_file)
counts <- read.csv(count_file, row.names = 1)

message("Loading metadata from: ", meta_file)
col_data <- read.csv(meta_file, row.names = 1)

# Validate that sample columns in counts match row names in metadata
if (!all(colnames(counts) == rownames(col_data))) {
  # Attempt to align them
  common_samples <- intersect(colnames(counts), rownames(col_data))
  if (length(common_samples) == 0) {
    stop("No common samples found between count matrix and metadata.")
  }
  message("Re-aligning samples. Found ", length(common_samples), " common samples.")
  counts <- counts[, common_samples]
  col_data <- col_data[common_samples, ]
}

# Determine design formula
# We assume 'condition' is the primary variable of interest.
# If 'batch' exists in metadata, include it in the design.
design_formula <- if ("batch" %in% colnames(col_data)) {
  ~ batch + condition
} else {
  ~ condition
}

message("Running DESeq2 with design: ", deparse(design_formula))

# Create DESeqDataSet
dds <- DESeqDataSetFromMatrix(
  countData = counts,
  colData = col_data,
  design = design_formula
)

# Filter out genes with very low counts (standard DESeq2 practice)
# Keep genes with at least 10 counts in at least 2 samples (or similar heuristic)
keep <- rowSums(counts(dds) >= 10) >= 2
dds <- dds[keep, ]

# Run DESeq
# This estimates size factors, dispersions, and fits the GLM
dds <- DESeq(dds)

# Extract results
# Contrast: condition vs reference. We assume the second level is the treatment vs first (reference).
# If the factor levels are not ordered, we take the last level as treatment vs first.
res <- results(dds)

# Convert to data frame for saving
res_df <- as.data.frame(res)
res_df$gene <- rownames(res_df)
# Reorder columns to put gene first
res_df <- res_df[, c("gene", setdiff(colnames(res_df), "gene"))]

# Save main results
results_path <- file.path(output_dir, "results.csv")
write.csv(res_df, results_path, row.names = FALSE)
message("Results saved to: ", results_path)

# Extract fixed dispersion parameters for US2 (Permutation Null Modeling)
# We need the gene-wise dispersion estimates and the fitted dispersion curve
disp_gene <- dispersions(dds)
disp_fit <- fitInfo(dds)$dispFit
mu_vals <- fitInfo(dds)$mu

disp_df <- data.frame(
  gene = names(disp_gene),
  dispersion = disp_gene,
  fitted_dispersion = disp_fit,
  mean_count = mu_vals
)
# Filter to only genes that survived filtering
disp_df <- disp_df[disp_df$gene %in% res_df$gene, ]

disp_path <- file.path(output_dir, "dispersion_params.csv")
write.csv(disp_df, disp_path, row.names = FALSE)
message("Dispersion parameters saved to: ", disp_path)

# Save model info for downstream logging
model_info <- list(
  design_formula = deparse(design_formula),
  n_samples = ncol(dds),
  n_genes = nrow(dds),
  coef_names = names(coefficients(dds)),
  run_time = Sys.time()
)
model_path <- file.path(output_dir, "model_info.json")
write_json(model_info, model_path, pretty = TRUE)
message("Model info saved to: ", model_path)

message("DESeq2 analysis complete.")