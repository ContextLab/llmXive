#!/usr/bin/env Rscript
#
# preprocess.R
# Performs QC (mitochondrial read filtering >20%) and normalization using Seurat v4.
# Outputs a normalized .h5ad file compatible with Python (scanpy/scvelo).
#
# Usage: Rscript preprocess.R --input <path> --output <path>

library(optparse)
library(Seurat)
library(SeuratDisk)
library(Matrix)

# Parse arguments
args <- commandArgs(trailingOnly = TRUE)
parser <- OptionParser()
parser$addOption("input", required = TRUE, help = "Input file path (e.g., .mtx, .h5)")
parser$addOption("output", required = TRUE, help = "Output file path (.h5ad)")

opts <- parser$parse(args)
input_path <- opts$input
output_path <- opts$output

cat(paste("Processing input:", input_path, "\n"))
cat(paste("Output to:", output_path, "\n"))

# Helper to load data (supports .mtx or .h5 from SRA download)
load_data <- function(path) {
  if (grepl("\\.mtx$", path, ignore.case = TRUE)) {
    # Assume standard Matrix Market format: matrix.mtx, genes.tsv, barcodes.tsv
    # Adjust path logic if download_data.py produces a specific folder structure
    dir_path <- dirname(path)
    mat <- ReadMtx(mtx = path,
                   features = paste0(dir_path, "/genes.tsv"),
                   cells = paste0(dir_path, "/barcodes.tsv"))
    return mat
  } else if (grepl("\\.h5$", path, ignore.case = TRUE)) {
    # If download_data.py produces .h5 directly
    mat <- Read10X_h5(path)
    return mat
  } else {
    stop(paste("Unsupported input format:", path))
  }
}

# Load data
tryCatch({
  raw_counts <- load_data(input_path)
}, error = function(e) {
  stop(paste("Failed to load data:", e$message))
})

# Create Seurat object
seurat_obj <- CreateSeuratObject(counts = raw_counts, project = "TCellExhaust")

# --- QC Step: Filter mitochondrial reads ---
# Calculate percent.mt
# Assuming gene names in the second column of features or row names contain 'MT-'
# Common convention: mitochondrial genes start with 'MT-' (human) or 'mt-' (mouse)
# We will calculate based on row names containing 'MT' (case insensitive)
mito_genes <- grep("^MT-", rownames(seurat_obj), ignore.case = TRUE)
if (length(mito_genes) == 0) {
  warning("No mitochondrial genes found starting with 'MT-'. Using fallback: genes containing 'MT'")
  mito_genes <- grep("MT", rownames(seurat_obj), ignore.case = TRUE)
}

if (length(mito_genes) > 0) {
  seurat_obj[["percent.mt"]] <- PercentageFeatureSet(seurat_obj, pattern = "^MT-", ignore.case = TRUE)
} else {
  warning("Could not identify mitochondrial genes. Skipping QC filter based on %mt.")
  seurat_obj[["percent.mt"]] <- 0
}

# Filter cells: >20% mitochondrial reads are REMOVED
# Keep cells where percent.mt <= 20
initial_cells <- ncells(seurat_obj)
seurat_obj <- subset(seurat_obj, subset = percent.mt <= 20)
final_cells <- ncells(seurat_obj)

cat(paste("Initial cells:", initial_cells, "\n"))
cat(paste("Cells after QC (<=20% mito):", final_cells, "\n"))

if (final_cells == 0) {
  stop("All cells filtered out by QC. Check input data or mitochondrial gene identification.")
}

# --- Normalization ---
# Standard Seurat normalization: LogNormalize
seurat_obj <- NormalizeData(seurat_obj, normalization.method = "LogNormalize", scale.factor = 10000)

# Find Variable Features
seurat_obj <- FindVariableFeatures(seurat_obj, selection.method = "vst", nfeatures = 2000)

# Scale Data (optional but good for downstream)
seurat_obj <- ScaleData(seurat_obj)

# --- Export to .h5ad ---
# SeuratDisk converts Seurat object to AnnData (.h5ad)
# We need to ensure the output directory exists
output_dir <- dirname(output_path)
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Convert and save
cat(paste("Converting to .h5ad and saving to:", output_path, "\n"))
tryCatch({
  Convert(seurat_obj, dest = "h5ad", filename = output_path)
}, error = function(e) {
  stop(paste("Failed to convert and save .h5ad:", e$message))
})

cat("Preprocessing completed successfully.\n")
