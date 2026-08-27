#!/usr/bin/env Rscript
# preprocess.R
# Performs QC (mitochondrial filter >20%) and normalization on raw count matrices
# using Seurat v4. Outputs normalized .h5ad files.
#
# Usage:
#   Rscript code/preprocess.R --input data/raw/GSE136103_raw_counts.rds --output data/processed/GSE136103_normalized.h5ad
#
# Prerequisites:
#   - R >= 4.3
#   - Seurat >= 4.0
#   - anndata (via reticulate)
#   - dplyr, stringr, Matrix

suppressPackageStartupMessages({
  library(Seurat)
  library(Matrix)
  library(dplyr)
  library(stringr)
  library(anndata)
  library(optparse)
})

# Parse command line arguments
option_list <- list(
  make_option(c("-i", "--input"), type = "character", default = NULL,
              help = "Path to input raw count matrix (RDS format with 'counts' object)"),
  make_option(c("-o", "--output"), type = "character", default = NULL,
              help = "Path to output normalized .h5ad file"),
  make_option(c("-p", "--percent.mt"), type = "double", default = 20.0,
              help = "Maximum percentage of mitochondrial reads allowed (default: 20)")
)

parser <- OptionParser(option_list = option_list)
args <- parse_args(parser)

if (is.null(args$input) || is.null(args$output)) {
  stop("Both --input and --output arguments are required.")
}

input_path <- args$input
output_path <- args$output
max_percent_mt <- args$percent.mt

# Verify input file exists
if (!file.exists(input_path)) {
  stop(paste("Input file not found:", input_path))
}

cat("Loading data from:", input_path, "\n")

# Load raw count matrix (expected format: RDS with a named list containing 'counts')
# The download_data.py or previous step should produce an RDS with a list: list(counts = <dgCMatrix>)
raw_data <- readRDS(input_path)

if (!is.list(raw_data) || !("counts" %in% names(raw_data))) {
  stop("Input RDS must contain a list with a 'counts' element (dgCMatrix).")
}

counts_matrix <- raw_data[["counts"]]

if (!is(counts_matrix, "dgCMatrix")) {
  stop("Counts matrix must be a dgCMatrix (sparse matrix).")
}

# Create Seurat object
cat("Creating Seurat object...\n")
seurat_obj <- CreateSeuratObject(
  counts = counts_matrix,
  project = "TCellExhaustion",
  min.cells = 3,
  min.features = 200
)

# Calculate mitochondrial percentage
# Assumes gene names in rownames are standard Ensembl or HGNC symbols.
# We try to detect mitochondrial genes by prefix "MT-" (human) or "mt-" (mouse).
# If none found, we look for common patterns or fail loudly if no MT genes detected.
features <- rownames(seurat_obj)
mt_pattern <- "^MT-"
if (!any(str_detect(features, mt_pattern))) {
  mt_pattern <- "^mt-"
  if (!any(str_detect(features, mt_pattern))) {
    # Fallback: try to detect by gene names if available in metadata, but standard is prefix
    stop("Could not detect mitochondrial genes (MT- or mt- prefix) in rownames. "
         "Please ensure gene names are standard human/mouse symbols.")
  }
}

mt_genes <- features[str_detect(features, mt_pattern)]
cat("Detected", length(mt_genes), "mitochondrial genes.\n")

seurat_obj[["percent.mt"]] <- PercentageFeatureSet(seurat_obj, pattern = mt_pattern)

# QC Filtering: Remove cells with > max_percent_mt mitochondrial reads
cat("Filtering cells with > ", max_percent_mt, "% mitochondrial reads...\n", sep="")
initial_cells <- ncol(seurat_obj)
seurat_obj <- subset(seurat_obj, subset = percent.mt < max_percent_mt)
final_cells <- ncol(seurat_obj)

cat("Initial cells:", initial_cells, "\n")
cat("Cells after QC:", final_cells, "\n")

if (final_cells == 0) {
  stop("QC filtering removed all cells. Check input data and mitochondrial threshold.")
}

# Normalization
cat("Normalizing data (SCTransform)...\n")
# Using SCTransform as it is robust and standard in Seurat v4
# If SCTransform fails due to memory, we can fallback to LogNormalize, but SCT is preferred for velocity
tryCatch({
  seurat_obj <- SCTransform(seurat_obj, verbose = FALSE)
}, error = function(e) {
  warning("SCTransform failed, falling back to LogNormalize: ", e$message)
  seurat_obj <- NormalizeData(seurat_obj, verbose = FALSE)
  seurat_obj <- FindVariableFeatures(seurat_obj, selection.method = "vst", nfeatures = 2000, verbose = FALSE)
})

# Prepare for export to .h5ad
# We need to extract the normalized counts.
# If SCT was used, the normalized data is in the 'SCT' assay, slot 'data'.
# If LogNormalize was used, it's in the 'RNA' assay, slot 'data'.
assay_name <- if ("SCT" %in% Assays(seurat_obj)) "SCT" else "RNA"
slot_name <- "data" # Normalized data

normalized_counts <- GetAssayData(seurat_obj, assay = assay_name, slot = slot_name)

# Convert to dense if small, but keep sparse for large to save memory
# anndataR expects a matrix (can be sparse)
# Ensure rownames and colnames are preserved
rownames(normalized_counts) <- rownames(seurat_obj)
colnames(normalized_counts) <- colnames(seurat_obj)

# Create AnnData object
cat("Creating AnnData object for export...\n")
# obs: cell metadata (percent.mt, nCount_RNA, nFeature_RNA)
obs_df <- seurat_obj@meta.data
# var: gene metadata (mean, dispersion for SCT, or just rownames)
var_df <- data.frame(
  gene_symbols = rownames(normalized_counts),
  row.names = rownames(normalized_counts)
)

# Construct AnnData
# Note: anndataR::AnnData expects X to be a matrix
# We use the normalized counts (sparse or dense)
ad <- AnnData(
  X = normalized_counts,
  obs = obs_df,
  var = var_df,
  uns = list()
)

# Write to .h5ad
cat("Writing output to:", output_path, "\n")
write_h5ad(ad, output_path)

cat("Preprocessing complete. Output written to:", output_path, "\n")
cat("Cells kept:", ncol(ad), "\n")
cat("Genes kept:", nrow(ad), "\n")

# Success
invisible(TRUE)