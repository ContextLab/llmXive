#!/usr/bin/env Rscript
#
# DESeq2/edgeR Differential Expression Analysis Script
#
# This script performs differential expression analysis and extracts
# fixed-dispersion parameters for permutation-based null modeling.
#
# Usage:
#   Rscript run_r_script.R --counts <path> --metadata <path> --output-dir <path>
#

library(argparse)
library(DESeq2)
library(data.table)
library(jsonlite)

# Parse command line arguments
parser <- ArgumentParser(description = "DESeq2/edgeR Differential Expression Analysis")
parser$add_argument("--counts", type = "character", required = TRUE,
                    help = "Path to input count matrix (CSV/TSV)")
parser$add_argument("--metadata", type = "character", required = TRUE,
                    help = "Path to sample metadata file")
parser$add_argument("--output-dir", type = "character", required = TRUE,
                    help = "Directory to save results")
args <- parser$parse_args()

# Ensure output directory exists
if (!dir.exists(args$output_dir)) {
  dir.create(args$output_dir, recursive = TRUE)
}

cat("Loading count data from:", args$counts, "\n")
cat("Loading metadata from:", args$metadata, "\n")
cat("Output directory:", args$output_dir, "\n")

# Load count matrix
# Expected format: rows = genes, columns = samples, first column = gene IDs
counts_df <- fread(args$counts, header = TRUE, sep = "auto")

# Extract gene IDs and convert to matrix
if (ncol(counts_df) < 2) {
  stop("Count matrix must have at least 2 columns (gene ID + counts)")
}

gene_ids <- counts_df[[1]]
count_matrix <- as.matrix(counts_df[, -1, with = FALSE])
rownames(count_matrix) <- gene_ids
colnames(count_matrix) <- paste0("Sample", 1:ncol(count_matrix))

cat("Loaded count matrix:", nrow(count_matrix), "genes x", ncol(count_matrix), "samples\n")

# Load metadata
metadata <- fread(args$metadata, header = TRUE, sep = "auto")

# Validate metadata
if (!"condition" %in% colnames(metadata)) {
  stop("Metadata must contain a 'condition' column for differential expression")
}

# Ensure metadata order matches count matrix columns
if (nrow(metadata) != ncol(count_matrix)) {
  stop("Number of samples in metadata (", nrow(metadata),
       ") does not match count matrix columns (", ncol(count_matrix), ")")
}

# Create DESeq2 dataset
coldata <- data.frame(
  row.names = colnames(count_matrix),
  condition = factor(metadata$condition)
)

# Create DESeqDataSet
dds <- DESeqDataSetFromMatrix(
  countData = count_matrix,
  colData = coldata,
  design = ~ condition
)

cat("Created DESeqDataSet with", nrow(dds), "genes and", ncol(dds), "samples\n")

# Filter low-count genes (keep genes with at least 10 counts in at least 2 samples)
keep <- rowSums(counts(dds) >= 10) >= 2
dds <- dds[keep, ]
cat("Filtered to", nrow(dds), "genes after low-count filtering\n")

# Run DESeq2 (this estimates dispersions)
cat("Running DESeq2 analysis...\n")
dds <- DESeq(dds, fitType = "local")

# Extract fixed dispersion parameters
# We use the estimated dispersions without refitting (fixed-dispersion approach)
dispersions <- dispersions(dds)
gene_ids <- rownames(dds)
mean_counts <- rowMeans(counts(dds, normalized = TRUE))

cat("Extracted dispersion parameters for", length(dispersions), "genes\n")

# Create output structure
dispersion_params <- list(
  gene_ids = as.character(gene_ids),
  dispersions = as.numeric(dispersions),
  mean_counts = as.numeric(mean_counts),
  design_formula = "~ condition",
  n_genes = length(gene_ids),
  n_samples = ncol(dds),
  n_conditions = length(levels(coldata$condition))
)

# Save dispersion parameters to JSON
output_file <- file.path(args$output_dir, "fixed_dispersion_params.json")
write_json(dispersion_params, output_file, pretty = TRUE, auto_unbox = TRUE)

cat("Saved dispersion parameters to:", output_file, "\n")

# Also save full results for reference (optional)
results_df <- as.data.frame(results(dds))
results_df$gene_id <- gene_ids
results_file <- file.path(args$output_dir, "deseq2_results.csv")
fwrite(results_df, results_file)

cat("Saved full DESeq2 results to:", results_file, "\n")
cat("Analysis complete.\n")
