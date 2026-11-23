#!/usr/bin/env Rscript
# Placeholder for R DE analysis script (DESeq2/edgeR)
# This script is called by Python modules for differential expression analysis.

args <- commandArgs(trailingOnly = TRUE)

if (length(args) < 2) {
    cat("Usage: run_r_script.R <count_matrix_path> <metadata_path> [output_dir]\n")
    quit(status = 1)
}

count_matrix_path <- args[1]
metadata_path <- args[2]
output_dir <- if (length(args) >= 3) args[3] else "."

# Load libraries
if (!require("DESeq2", quietly = TRUE)) {
    stop("DESeq2 package not found. Please install it.")
}

# Read data
counts <- read.table(count_matrix_path, header = TRUE, row.names = 1)
metadata <- read.table(metadata_path, header = TRUE, row.names = 1)

# Create DESeqDataSet
dds <- DESeqDataSetFromMatrix(countData = counts,
                              colData = metadata,
                              design = ~ condition)

# Run DESeq
dds <- DESeq(dds)
results <- results(dds)

# Save results
output_file <- file.path(output_dir, "de_results.csv")
write.csv(as.data.frame(results), output_file)

cat("DE analysis completed. Results saved to:", output_file, "\n")
