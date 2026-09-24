#!/usr/bin/env Rscript
#
# code/03c_extract_peak_signals.R
#
# Task: T007c
# Description: Extract normalized peak signal (RPKM/counts) for each TF-condition
#              pair from the BAM files (output of T006) for all CREs in
#              data/processed/CRE_merged.bed.
# Output: data/processed/peak_signal_matrix.tsv
#
# Dependencies:
#   - Rsamtools (for BAM access)
#   - rtracklayer (for BED import)
#   - GenomicRanges (for overlap operations)
#   - dplyr (for data manipulation)
#   - data.table (for fast I/O)
#
# Input Files:
#   - data/processed/CRE_merged.bed (from T008)
#   - BAM files listed in data/manifest.yaml (from T005)
#
# Output File:
#   - data/processed/peak_signal_matrix.tsv (columns: cre_id, tf_id, condition, signal)
#
# Notes:
#   - Signal is computed as RPKM (Reads Per Kilobase per Million mapped reads).
#   - Requires the BAM files to be indexed (.bai) and located in data/processed/bam/
#     or as specified in the manifest.
#   - This script fails loudly if inputs are missing (no synthetic fallback).

library(Rsamtools)
library(rtracklayer)
library(GenomicRanges)
library(dplyr)
library(data.table)
library(yaml)

# --- Configuration ---
CRE_BED_PATH <- "data/processed/CRE_merged.bed"
MANIFEST_PATH <- "data/manifest.yaml"
OUTPUT_PATH <- "data/processed/peak_signal_matrix.tsv"
BAM_DIR <- "data/processed/bam" # Standard location per T005/T006

# --- Helper Functions ---

log_msg <- function(msg, level = "INFO") {
  timestamp <- format(Sys.time(), "%Y-%m-%dT%H:%M:%S")
  cat(sprintf("[%s] %s: %s\n", timestamp, level, msg))
}

# Load manifest to find BAM paths
load_manifest_bams <- function(manifest_path) {
  if (!file.exists(manifest_path)) {
    stop(sprintf("Manifest file not found: %s", manifest_path))
  }
  manifest <- yaml.load_file(manifest_path)
  # Expecting a structure like: data: { chipseq: { runs: [ {run_id, file_path, ...} ] } }
  # Adapt based on actual manifest structure if needed.
  # Assuming standard structure derived from T005/T006:
  # manifest$data$chipseq$runs is a list of data frames or lists containing file paths.
  
  runs <- manifest$data$chipseq$runs
  if (is.null(runs)) {
    stop("Manifest does not contain chipseq runs data.")
  }
  
  bam_files <- list()
  for (run in runs) {
    # Determine file path. Could be 'file_path', 'path', or constructed from base + filename.
    # Assuming 'file_path' exists in the manifest entry as per T005 output.
    # Also need to map to tf_id and condition.
    # Manifest structure assumption:
    # runs:
    #   - run_id: SRR123
    #     tf_id: TF1
    #     condition: heatshock
    #     file_path: data/processed/bam/SRR123.bam
    
    file_path <- run$file_path
    if (is.null(file_path)) next
    
    if (!file.exists(file_path)) {
      # Try constructing path if relative
      if (!file.exists(file_path) && file.exists(file.path(BAM_DIR, basename(file_path)))) {
        file_path <- file.path(BAM_DIR, basename(file_path))
      }
    }
    
    if (!file.exists(file_path)) {
      stop(sprintf("BAM file not found for run %s: %s", run$run_id, file_path))
    }
    
    # Check for index
    bai_path <- paste0(file_path, ".bai")
    if (!file.exists(bai_path)) {
      stop(sprintf("BAM index not found for %s: %s", run$run_id, bai_path))
    }
    
    bam_files[[length(bam_files) + 1]] <- list(
      run_id = run$run_id,
      tf_id = run$tf_id,
      condition = run$condition,
      file_path = file_path
    )
  }
  
  if (length(bam_files) == 0) {
    stop("No valid BAM files found in manifest.")
  }
  
  return(bam_files)
}

# Calculate RPKM for a specific GRanges region against a BAM file
calculate_rpkms <- function(bam_file, regions) {
  # Count overlaps
  param <- ScanBamParam(which=regions, what=c("qwidth"))
  # We just need the count of fragments/reads overlapping the region
  # Using countOverlaps directly on the BAM might be heavy, so we use Rsamtools
  # to get the reads, then count.
  
  # Efficient approach: countOverlaps on the GRanges from BAM
  # But loading all reads is memory heavy. 
  # Alternative: Use summarizeOverlaps if we had a SummarizedExperiment, 
  # but here we just need counts per region.
  
  # Let's use countOverlaps with a BamFileList or iterate.
  # Given the constraint of "real data" and potential size, we iterate.
  
  bam <- BamFile(bam_file, index = paste0(bam_file, ".bai"))
  
  # Get total mapped reads for normalization (once per BAM)
  # This is expensive if done repeatedly, so we cache it.
  # However, we need it for RPKM.
  total_mapped <- countBam(bam)$records
  
  if (total_mapped == 0) {
    warning(sprintf("BAM file %s has 0 mapped reads.", bam_file))
    return(rep(0, length(regions)))
  }
  
  # Count reads overlapping each region
  # We need to count fragments. Assuming paired-end, we count fragments.
  # countBam counts fragments if paired-end is handled correctly, but countOverlaps
  # on the BAM file is tricky.
  # Standard practice: Use countOverlaps on the GRanges of the reads? No, too slow.
  # Use summarizeOverlaps?
  
  # Simpler approach for this script:
  # 1. Import regions.
  # 2. Use countOverlaps on the BAM file by reading reads? No.
  # 3. Use the `summarizeOverlaps` function from GenomicAlignments.
  
  # Let's use GenomicAlignments::summarizeOverlaps
  # It's robust for RPKM/FPKM calculations.
  
  # However, to avoid loading all reads into memory, we use the "Union" mode
  # and let it stream.
  
  # Actually, for a simple script, counting overlaps with countOverlaps on a 
  # GRanges object of reads is the most straightforward if we can get the reads.
  # But for large BAMs, we must stream.
  
  # Let's use the `Rsamtools` `countBam` with a specific `which` argument.
  # We can call countBam for each region? That's N calls.
  # Or pass the whole GRanges to `which`.
  
  counts <- countBam(bam, param = ScanBamParam(which = regions))
  # countBam returns a data.frame with 'records' (total) and 'mapped' etc.
  # But we need counts PER region.
  # countBam with 'which' as a GRanges returns a list of counts?
  # Actually, countBam with a GRanges 'which' returns a vector of counts if 'which' is a GRanges.
  # Let's verify: countBam(file, param=ScanBamParam(which=gr)) -> returns a list?
  # Documentation: "If which is a GRanges, the result is a list of counts."
  # No, it returns a data.frame if multiple files, or a list if one file and multiple regions?
  # Let's assume it returns a vector of counts if we pass a GRanges.
  # Wait, `countBam` with `which` as GRanges returns a list of counts for each range?
  # Actually, the return value of countBam is a data.frame if multiple files, or a named list?
  # Let's use a safer method: iterate over regions if countBam doesn't support vectorized counts per region easily.
  # But for performance, we try to do it in one go.
  
  # Correct usage:
  # param <- ScanBamParam(which=regions)
  # res <- countBam(bam, param=param)
  # This returns a data.frame with columns: file, records, mapped, etc.
  # It does NOT return per-region counts if 'which' is a GRanges of multiple regions.
  # It sums them up.
  
  # We need per-region counts.
  # Approach: Use `summarizeOverlaps` from GenomicAlignments.
  # It is designed for this.
  
  # But `summarizeOverlaps` requires a `reads` object.
  # We can use `BamFile` as the input.
  
  # Let's try to use `summarizeOverlaps` with mode="Union".
  # It will count fragments overlapping the features.
  
  # However, `summarizeOverlaps` might load all reads? No, it streams.
  
  # Let's implement a manual loop if `summarizeOverlaps` is too heavy on dependencies or complex.
  # But we are in R, so we should use the ecosystem.
  
  # Alternative: Use `GenomicAlignments::readGAlignments` with `which`?
  # No, that loads reads.
  
  # Let's go with `countBam` but iterate over regions if necessary.
  # Given the constraint of "real data" and "no stubs", we must be correct.
  # Iterating over thousands of regions with `countBam` is slow but correct.
  # If regions are many, we might need a faster method.
  # But for a research pipeline, correctness is key.
  
  # Let's try to use `summarizeOverlaps` which is the standard.
  # It takes a `features` (GRanges) and a `files` (BamFile).
  
  # We need to load GenomicAlignments.
  if (!requireNamespace("GenomicAlignments", quietly = TRUE)) {
    stop("GenomicAlignments package is required for accurate fragment counting.")
  }
  library(GenomicAlignments)
  
  # Count fragments
  # We assume the BAM is paired-end. If single-end, it counts reads.
  # summarizeOverlaps handles this via 'fragments' argument?
  # Default is to count fragments for paired-end.
  
  se <- summarizeOverlaps(features = regions,
                          reads = bam,
                          mode = "Union",
                          singleEnd = FALSE, # Assume paired-end as per T006
                          fragments = TRUE,
                          ignore.strand = TRUE)
  
  counts <- assay(se)[,1]
  
  # RPKM = (count / (region_length_kb * total_mapped_millions))
  # region_length in kb
  region_lengths_kb <- width(regions) / 1000
  total_mapped_millions <- total_mapped / 1e6
  
  # Avoid division by zero
  total_mapped_millions <- ifelse(total_mapped_millions == 0, 1, total_mapped_millions)
  
  rpkm <- counts / (region_lengths_kb * total_mapped_millions)
  
  return(rpkm)
}

# --- Main Execution ---

main <- function() {
  log_msg("Starting peak signal extraction (T007c)...")
  
  # 1. Load CREs
  if (!file.exists(CRE_BED_PATH)) {
    stop(sprintf("CRE merged BED file not found: %s. Ensure T008 has run.", CRE_BED_PATH))
  }
  
  log_msg(sprintf("Loading CREs from %s", CRE_BED_PATH))
  cre_gr <- import(CRE_BED_PATH)
  
  # Ensure we have a cre_id column. T008 should have provided 'name' or 'gene_id'.
  # Assuming the 4th column of BED is the name (cre_id).
  if (is.null(mcols(cre_gr)$name)) {
    # If not, try gene_id or create one
    if (!is.null(mcols(cre_gr)$gene_id)) {
      mcols(cre_gr)$cre_id <- mcols(cre_gr)$gene_id
    } else {
      mcols(cre_gr)$cre_id <- paste0("CRE_", seq_along(cre_gr))
    }
  } else {
    mcols(cre_gr)$cre_id <- mcols(cre_gr)$name
  }
  
  log_msg(sprintf("Loaded %d CREs.", length(cre_gr)))
  
  # 2. Load Manifest and BAMs
  log_msg(sprintf("Loading manifest from %s", MANIFEST_PATH))
  bam_list <- load_manifest_bams(MANIFEST_PATH)
  log_msg(sprintf("Found %d BAM files.", length(bam_list)))
  
  # 3. Iterate and Extract Signals
  results <- list()
  
  for (bam_info in bam_list) {
    log_msg(sprintf("Processing %s (TF: %s, Condition: %s)...", 
                    bam_info$run_id, bam_info$tf_id, bam_info$condition))
    
    tryCatch({
      rpkm_vals <- calculate_rpkms(bam_info$file_path, cre_gr)
      
      # Create a data frame for this run
      df <- data.frame(
        cre_id = mcols(cre_gr)$cre_id,
        tf_id = bam_info$tf_id,
        condition = bam_info$condition,
        signal = rpkm_vals,
        stringsAsFactors = FALSE
      )
      results[[length(results) + 1]] <- df
    }, error = function(e) {
      log_msg(sprintf("Error processing %s: %s", bam_info$run_id, e$message), "ERROR")
      # Fail loudly
      stop(e)
    })
  }
  
  # 4. Combine and Write
  if (length(results) == 0) {
    stop("No signals were extracted. Check BAM files and regions.")
  }
  
  final_df <- bind_rows(results)
  
  # Ensure output directory exists
  out_dir <- dirname(OUTPUT_PATH)
  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE)
  }
  
  log_msg(sprintf("Writing output to %s", OUTPUT_PATH))
  write.table(final_df, 
              file = OUTPUT_PATH, 
              sep = "\t", 
              quote = FALSE, 
              row.names = FALSE)
  
  log_msg("Task T007c completed successfully.")
}

main()
