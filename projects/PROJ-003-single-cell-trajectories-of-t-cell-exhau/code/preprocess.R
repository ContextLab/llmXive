#!/usr/bin/env Rscript
#
# preprocess.R
# Performs QC (mitochondrial read filtering >20%) and normalization
# using Seurat v4. Outputs a normalized .h5ad file compatible with
# Python (scanpy/scvelo).
#
# Usage: Rscript preprocess.R --input <path> --output <path>

args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(flag) {
  i <- match(flag, args)
  if (!is.na(i) && length(args) >= i + 1) return(args[i + 1])
  return(NULL)
}
input_path <- get_arg("--input")
output_path <- get_arg("--output")
if (is.null(input_path) || is.null(output_path)) {
  stop("--input and --output are required arguments")
}

cat(paste("Processing input:", input_path, "\n"))
cat(paste("Output to:", output_path, "\n"))

suppressPackageStartupMessages({
  library(Seurat)
  library(Matrix)
})

# Helper to load data (supports .mtx or 10x .h5 from the download step)
load_data <- function(path) {
  if (grepl("\\.mtx(\\.gz)?$", path, ignore.case = TRUE)) {
    dir_path <- dirname(path)
    genes_file <- file.path(dir_path, "genes.tsv")
    barcodes_file <- file.path(dir_path, "barcodes.tsv")
    if (file.exists(genes_file) && file.exists(barcodes_file)) {
      mat <- ReadMtx(mtx = path, features = genes_file,
                     cells = barcodes_file)
    } else {
      mat <- ReadMtx(mtx = path)
    }
    return(mat)
  } else if (grepl("\\.h5$", path, ignore.case = TRUE)) {
    mat <- Read10X_h5(path)
    return(mat)
  } else {
    stop(paste("Unsupported input format for R path:", path,
               "(use the Python wrapper for delimited matrices)"))
  }
}

# Load data
raw_counts <- tryCatch(
  load_data(input_path),
  error = function(e) stop(paste("Failed to load data:", e$message))
)

# Create Seurat object
seurat_obj <- CreateSeuratObject(counts = raw_counts, project = "TCellExhaust")

# --- QC Step: Filter mitochondrial reads (>20% removed) ---
mito_pattern <- "^MT-"
if (length(grep(mito_pattern, rownames(seurat_obj))) == 0) {
  mito_pattern <- "^mt-"
}
if (length(grep(mito_pattern, rownames(seurat_obj))) == 0) {
  warning("No mitochondrial genes found; percent.mt set to 0.")
  seurat_obj[["percent.mt"]] <- 0
} else {
  seurat_obj[["percent.mt"]] <- PercentageFeatureSet(
    seurat_obj, pattern = mito_pattern
  )
}

initial_cells <- ncol(seurat_obj)
seurat_obj <- subset(seurat_obj, subset = percent.mt <= 20)
final_cells <- ncol(seurat_obj)

cat(paste("Initial cells:", initial_cells, "\n"))
cat(paste("Cells after QC (<=20% mito):", final_cells, "\n"))

if (final_cells == 0) {
  stop("All cells filtered out by QC. Check input data or mitochondrial gene identification.")
}

# --- Normalization (Seurat v4 defaults) ---
seurat_obj <- NormalizeData(seurat_obj,
                            normalization.method = "LogNormalize",
                            scale.factor = 10000)
seurat_obj <- FindVariableFeatures(seurat_obj,
                                   selection.method = "vst",
                                   nfeatures = 2000)
seurat_obj <- ScaleData(seurat_obj)

# --- Export to .h5ad ---
output_dir <- dirname(output_path)
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

cat(paste("Converting to .h5ad and saving to:", output_path, "\n"))
tryCatch({
  if (!requireNamespace("SeuratDisk", quietly = TRUE)) {
    stop("SeuratDisk package is required for .h5ad export. Install with remotes::install_github('mojaveazure/seurat-disk')")
  }
  Convert(seurat_obj, dest = "h5ad", filename = output_path)
}, error = function(e) {
  stop(paste("Failed to convert and save .h5ad:", e$message))
})

cat("Preprocessing completed successfully.\n")
