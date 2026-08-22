#!/usr/bin/env Rscript
#
# run_de_per_tumor.R
# Implements Per-Tumor-Type DE Execution for User Story 2.
#
# Logic:
# 1. Load the split discovery set (processed counts and phenotypes).
# 2. Identify unique tumor types present in the discovery set.
# 3. For each tumor type:
#    a. Subset data to that tumor type.
#    b. Run DESeq2 differential expression analysis (Response vs Non-Response).
#    c. Extract results (log2FC, p-value, adjusted p-value).
#    d. Save results to a CSV file in results/discovery_de/.
#
# This script is invoked by the Python orchestrator (src/biomarker_discovery.py
# or src/differential_expression.py) via rpy2.
#

# Suppress specific warnings for cleaner output unless debugging
options(warn = -1)

# Load required libraries
if (!requireNamespace("DESeq2", quietly = TRUE)) {
  stop("Package 'DESeq2' is required but not installed. Please install it.")
}
if (!requireNamespace("SummarizedExperiment", quietly = TRUE)) {
  stop("Package 'SummarizedExperiment' is required but not installed.")
}
if (!requireNamespace("Biobase", quietly = TRUE)) {
  stop("Package 'Biobase' is required but not installed.")
}

library(DESeq2)
library(SummarizedExperiment)
library(Biobase)
library(tools) # for file_path_sans_ext if needed, though we use base R mostly

# Function to setup R environment (called by Python if needed, but mostly internal)
setup_r_environment <- function() {
  # Ensure locale is set to avoid encoding issues
  Sys.setlocale("LC_ALL", "C")
}

# Function to load discovery set data
# Expected input files:
# - data/processed/discovery_counts.csv (or similar, passed as arg)
# - data/processed/discovery_phenotypes.csv (or similar, passed as arg)
load_discovery_set <- function(counts_path, phenotypes_path) {
  if (!file.exists(counts_path)) {
    stop(paste("Counts file not found:", counts_path))
  }
  if (!file.exists(phenotypes_path)) {
    stop(paste("Phenotypes file not found:", phenotypes_path))
  }

  counts_df <- read.csv(counts_path, row.names = 1, check.names = FALSE)
  pheno_df <- read.csv(phenotypes_path, row.names = 1, check = FALSE)

  # Ensure row names match between counts and phenotypes
  common_samples <- intersect(colnames(counts_df), rownames(pheno_df))
  if (length(common_samples) == 0) {
    stop("No common samples found between counts and phenotypes.")
  }

  counts_df <- counts_df[, common_samples]
  pheno_df <- pheno_df[common_samples, , drop = FALSE]

  # Create DESeqDataSet
  dds <- DESeqDataSetFromMatrix(
    countData = counts_df,
    colData = pheno_df,
    design = ~ response_label
  )

  return(dds)
}

# Function to run DESeq2 analysis for a specific tumor type
# If tumor_type is NULL, runs on the whole dataset (used for single-type datasets)
run_deseq2_analysis <- function(dds, tumor_type = NULL) {
  # Subset if a specific tumor type is requested
  if (!is.null(tumor_type)) {
    # Check if tumor_type column exists in colData
    if (!"tumor_type" %in% colnames(colData(dds))) {
      stop("Column 'tumor_type' not found in colData. Cannot subset by tumor type.")
    }
    # Filter samples
    keep_samples <- colData(dds)$tumor_type == tumor_type
    if (sum(keep_samples) == 0) {
      warning(paste("No samples found for tumor type:", tumor_type))
      return(NULL)
    }
    dds <- dds[, keep_samples]
  }

  # Check for sufficient samples for DESeq2 (at least 2 per condition ideally)
  conditions <- colData(dds)$response_label
  table_conditions <- table(conditions)
  if (any(table_conditions < 2)) {
    warning("Insufficient samples in one or more response groups for DESeq2. Skipping.")
    return(NULL)
  }

  # Run DESeq2
  # We use a try-catch to handle potential errors during model fitting
  tryCatch({
    dds <- DESeq(dds)
    res <- results(dds, alpha = 0.05) # Default FDR threshold
    
    # Convert to data frame
    res_df <- as.data.frame(res)
    res_df$gene_id <- rownames(res_df)
    
    # Reset row names for cleaner export
    rownames(res_df) <- NULL
    
    return(res_df)
  }, error = function(e) {
    warning(paste("DESeq2 analysis failed for tumor type:", 
                  ifelse(is.null(tumor_type), "ALL", tumor_type), 
                  "Error:", e$message))
    return(NULL)
  })
}

# Main execution function
# Arguments passed from Python:
# 1. counts_path: Path to discovery counts CSV
# 2. phenotypes_path: Path to discovery phenotypes CSV
# 3. output_dir: Directory to save results
# 4. tumor_types_json: JSON string list of tumor types to process (optional, if NULL process all)
main <- function(args) {
  if (length(args) < 4) {
    stop("Usage: Rscript run_de_per_tumor.R <counts_path> <phenotypes_path> <output_dir> [tumor_types_json]")
  }

  counts_path <- args[1]
  phenotypes_path <- args[2]
  output_dir <- args[3]
  tumor_types_json <- if (length(args) > 4) args[4] else NULL

  # Ensure output directory exists
  if (!dir.exists(output_dir)) {
    dir.create(output_dir, recursive = TRUE)
  }

  # Load data
  message("Loading discovery set...")
  dds <- load_discovery_set(counts_path, phenotypes_path)

  # Determine tumor types to process
  if (!is.null(tumor_types_json)) {
    tumor_types <- jsonlite::fromJSON(tumor_types_json)
  } else {
    # If not specified, extract unique tumor types from the dataset
    if ("tumor_type" %in% colnames(colData(dds))) {
      tumor_types <- unique(colData(dds)$tumor_type)
    } else {
      # If no tumor_type column, treat the whole dataset as one type (or skip)
      # For this pipeline, we expect tumor_type to be present after splitting
      tumor_types <- c("ALL") 
    }
  }

  message(paste("Processing", length(tumor_types), "tumor types..."))

  results_list <- list()

  for (tt in tumor_types) {
    message(paste("Running DE for tumor type:", tt))
    
    # Run DE
    res_df <- run_deseq2_analysis(dds, tumor_type = tt)
    
    if (!is.null(res_df)) {
      # Define output filename
      safe_tt <- gsub("[^[:alnum:]_-]", "_", tt)
      out_file <- file.path(output_dir, paste0("de_results_", safe_tt, ".csv"))
      
      # Write results
      write.csv(res_df, file = out_file, row.names = FALSE)
      message(paste("Saved results to:", out_file))
      
      results_list[[tt]] <- out_file
    } else {
      message(paste("Skipped tumor type:", tt, "due to insufficient data or errors."))
    }
  }

  # Return list of output files for the Python orchestrator to aggregate
  # In a script context, we just print them or return via invisible()
  # The Python wrapper will read the generated files directly from the directory
  invisible(results_list)
}

# Parse command line arguments
args <- commandArgs(trailingOnly = TRUE)
if (length(args) > 0) {
  main(args)
}

# Export functions for rpy2 if called programmatically
# (These are already defined in the global environment of the script)
# setup_r_environment
# load_discovery_set
# run_deseq2_analysis
# main