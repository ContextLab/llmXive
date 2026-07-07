#!/bin/bash
set -euo pipefail

# Task T009b: Compute signal in null regions
# Input:  data/processed/null_regions.bed (from T009a)
# Input:  data/intermediate/aligned_sorted.bam (from T006/T007 pipeline)
# Output: data/processed/null_region_signal.bed
#
# This script calculates the read coverage (signal) within the defined null regions.
# It uses bedtools coverage to count reads overlapping each null region.
# It assumes the BAM files are already aligned and sorted (produced by T006/T007).
# If multiple BAMs exist (e.g., per condition), it sums them or processes the merged BAM.
# For this implementation, we expect a merged BAM at data/intermediate/merged_chipseq.bam
# or process the first available BAM if specific merging isn't done yet.
# To be robust, we will look for the merged BAM. If not found, we fail loudly.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

NULL_REGIONS="${PROJECT_ROOT}/data/processed/null_regions.bed"
MERGED_BAM="${PROJECT_ROOT}/data/intermediate/merged_chipseq.bam"

# Fallback: if merged BAM doesn't exist, try to find any sorted BAM in intermediate
if [[ ! -f "$MERGED_BAM" ]]; then
    MERGED_BAM=$(find "${PROJECT_ROOT}/data/intermediate" -name "*.bam" -type f | head -n 1)
    if [[ -z "$MERGED_BAM" ]]; then
        echo "ERROR: No BAM files found in data/intermediate/ to compute signal against."
        echo "Ensure T006 (preprocess) and T007 (peak calling) have run to generate BAMs."
        exit 1
    fi
    echo "WARNING: Merged BAM not found. Using first available BAM: $MERGED_BAM"
fi

OUTPUT_FILE="${PROJECT_ROOT}/data/processed/null_region_signal.bed"

if [[ ! -f "$NULL_REGIONS" ]]; then
    echo "ERROR: Null regions file not found: $NULL_REGIONS"
    echo "Please run T009a (06a_define_null_regions.sh) first."
    exit 1
fi

echo "Computing signal for null regions..."
echo "Input BAM: $MERGED_BAM"
echo "Input Regions: $NULL_REGIONS"
echo "Output: $OUTPUT_FILE"

# Ensure output directory exists
mkdir -p "$(dirname "$OUTPUT_FILE")"

# Use bedtools coverage to calculate signal
# -a: null regions (bed)
# -b: BAM file
# -counts: return number of overlaps (signal)
# -sorted: optimization if files are sorted (null_regions is likely sorted)
# Output format: chrom, start, end, count
# We will add a header or ensure the output is clean.

bedtools coverage -a "$NULL_REGIONS" -b "$MERGED_BAM" -counts > "$OUTPUT_FILE"

# Verify output is not empty
if [[ ! -s "$OUTPUT_FILE" ]]; then
    echo "ERROR: Output file $OUTPUT_FILE is empty. Check input BAM and region coordinates."
    exit 1
fi

echo "SUCCESS: Null region signal computed and saved to $OUTPUT_FILE"
echo "First 5 lines of output:"
head -n 5 "$OUTPUT_FILE"
