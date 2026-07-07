#!/bin/bash
set -euo pipefail

# Task T008: Merge peaks across TFs/conditions and annotate promoter vs distal
# Input: Individual peak BED files from T007 (code/03_call_peaks.sh)
# Output: data/processed/CRE_merged.bed
#
# Requirements (FR-004):
# 1. Merge overlapping peaks across all TFs/conditions
# 2. Annotate as "promoter" if within 500bp of a TSS, otherwise "distal"
# 3. Output format: chrom, start, end, type, source_count, source_list

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/data/processed"
INPUT_DIR="${DATA_DIR}/peaks"
OUTPUT_FILE="${DATA_DIR}/CRE_merged.bed"
TSS_FILE="${DATA_DIR}/annotation/yeast_tss.bed"

# Check dependencies
command -v bedtools >/dev/null 2>&1 || { echo "Error: bedtools is required but not installed."; exit 1; }
command -v awk >/dev/null 2>&1 || { echo "Error: awk is required but not installed."; exit 1; }

# Validate input directory
if [[ ! -d "${INPUT_DIR}" ]]; then
    echo "Error: Input directory ${INPUT_DIR} not found. Run T007 (03_call_peaks.sh) first."
    exit 1
fi

# Validate TSS file exists
if [[ ! -f "${TSS_FILE}" ]]; then
    echo "Error: TSS annotation file ${TSS_FILE} not found."
    echo "Please ensure TSS coordinates are available in data/processed/annotation/yeast_tss.bed"
    exit 1
fi

# Create output directory if needed
mkdir -p "${DATA_DIR}"
mkdir -p "$(dirname "${OUTPUT_FILE}")"

echo "Starting peak merge and annotation..."
echo "Input directory: ${INPUT_DIR}"
echo "Output file: ${OUTPUT_FILE}"
echo "TSS reference: ${TSS_FILE}"

# Step 1: Concatenate all peak files and extract unique regions
# Assuming input files are .bed or .narrowPeak format
# We take the first 3 columns (chrom, start, end) for merging
echo "Concatenating peak files..."
cat "${INPUT_DIR}"/*.bed "${INPUT_DIR}"/*.narrowPeak 2>/dev/null | \
    awk 'BEGIN{OFS="\t"} {print $1, $2, $3}' | \
    sort -k1,1 -k2,2n > "${DATA_DIR}/tmp_peaks_all.bed"

# Step 2: Merge overlapping peaks
echo "Merging overlapping peaks..."
bedtools merge -i "${DATA_DIR}/tmp_peaks_all.bed" > "${DATA_DIR}/tmp_merged.bed"

# Step 3: Annotate as promoter or distal based on TSS proximity
# Promoter: within 500bp of TSS (either upstream or downstream)
# We use bedtools closest to find the nearest TSS for each merged peak
echo "Annotating promoter vs distal regions..."

# Create a TSS window file (TSS - 500bp to TSS + 500bp)
# Assuming TSS file has: chrom, start, end, gene_id, score, strand
# We expand TSS to 500bp upstream and downstream
awk 'BEGIN{OFS="\t"} {
    start = $2 - 500;
    if (start < 0) start = 0;
    end = $3 + 500;
    print $1, start, end, $4, $5, $6
}' "${TSS_FILE}" | sort -k1,1 -k2,2n > "${DATA_DIR}/tmp_tss_promoters.bed"

# Find overlaps between merged peaks and promoter windows
# -wa: write the original A entry (merged peak)
# -wb: write the original B entry (promoter window)
# -u: write A once for each overlap (we just need to know if there is an overlap)
bedtools intersect -a "${DATA_DIR}/tmp_merged.bed" -b "${DATA_DIR}/tmp_tss_promoters.bed" -wa -u > "${DATA_DIR}/tmp_promoter_peaks.bed"

# Get count of promoter peaks
promoter_count=$(wc -l < "${DATA_DIR}/tmp_promoter_peaks.bed")
total_count=$(wc -l < "${DATA_DIR}/tmp_merged.bed")
distal_count=$((total_count - promoter_count))

echo "Total merged peaks: ${total_count}"
echo "Promoter peaks (<=500bp from TSS): ${promoter_count}"
echo "Distal peaks (>500bp from TSS): ${distal_count}"

# Step 4: Generate final output with annotation
# Format: chrom, start, end, type, source_count, source_list
# We need to count how many original peaks contributed to each merged region
# and list the sources

# First, re-merge with counts and source tracking
# Using bedtools merge with -c and -o options
# We need to include the source file name in the input
echo "Tracking source files for each peak..."

# Create a file with peak regions and source info
> "${DATA_DIR}/tmp_peaks_with_source.bed"
for file in "${INPUT_DIR}"/*.bed "${INPUT_DIR}"/*.narrowPeak; do
    if [[ -f "$file" ]]; then
        filename=$(basename "$file")
        # Extract just the TF/condition name if possible, otherwise use filename
        source_name="${filename%.*}"
        awk -v src="${source_name}" 'BEGIN{OFS="\t"} {print $1, $2, $3, src}' "$file" >> "${DATA_DIR}/tmp_peaks_with_source.bed"
    fi
done

# Sort by chrom, start
sort -k1,1 -k2,2n "${DATA_DIR}/tmp_peaks_with_source.bed" > "${DATA_DIR}/tmp_peaks_with_source_sorted.bed"

# Merge with counts and source list
# -c 4: count the source column
# -o 4: concatenate the source names
# -delim "," : separate sources with comma
bedtools merge -i "${DATA_DIR}/tmp_peaks_with_source_sorted.bed" -c 4 -o count,distinct -delim "," > "${DATA_DIR}/tmp_merged_with_info.bed"

# Step 5: Join with promoter annotation and create final output
# Left join: all merged peaks, with promoter info where available
sort -k1,1 -k2,2n "${DATA_DIR}/tmp_merged.bed" > "${DATA_DIR}/tmp_merged_sorted.bed"
sort -k1,1 -k2,2n "${DATA_DIR}/tmp_promoter_peaks.bed" > "${DATA_DIR}/tmp_promoter_sorted.bed"

# Use bedtools intersect to mark promoters, then awk to format
echo "chrom\tstart\tend\ttype\tsource_count\tsource_list" > "${OUTPUT_FILE}"

bedtools intersect -a "${DATA_DIR}/tmp_merged_sorted.bed" -b "${DATA_DIR}/tmp_promoter_sorted.bed" -wa -wb > "${DATA_DIR}/tmp_promoter_overlap.bed" 2>/dev/null || true

# Process the merged file with info
# tmp_merged_with_info.bed format: chrom, start, end, source_count, source_list
awk 'BEGIN{OFS="\t"} {
    chrom = $1;
    start = $2;
    end = $3;
    source_count = $4;
    source_list = $5;

    # Check if this region is a promoter (exists in promoter_overlap)
    # We need to check if this region overlaps with any promoter region
    is_promoter = 0;
}' "${DATA_DIR}/tmp_merged_with_info.bed" > /dev/null # Just validating format

# Better approach: create a lookup for promoter regions
# Since bedtools merge output doesn't preserve exact coordinates for lookup,
# we'll use bedtools intersect with the original merged file and promoter regions

# Create a temporary file with merged regions and their types
bedtools intersect -a "${DATA_DIR}/tmp_merged_sorted.bed" -b "${DATA_DIR}/tmp_promoter_sorted.bed" -wa > "${DATA_DIR}/tmp_promoter_regions.bed" 2>/dev/null || touch "${DATA_DIR}/tmp_promoter_regions.bed"

# Now join with the info file
# We'll use a simple approach: iterate through merged_with_info and check overlap
# Since bedtools doesn't easily support this join, we'll use a Python one-liner or awk with lookup

# Create a set of promoter regions for lookup
# Format: chrom:start-end
awk 'BEGIN{OFS="\t"} {print $1":"$2"-"$3}' "${DATA_DIR}/tmp_promoter_regions.bed" | sort -u > "${DATA_DIR}/tmp_promoter_keys.txt"

# Process merged_with_info and annotate
awk 'BEGIN{OFS="\t"}
FILENAME == ARGV[1] {
    promoter_regions[$1] = 1;
    next;
}
{
    key = $1":"$2"-"$3;
    if (key in promoter_regions) {
        type = "promoter";
    } else {
        type = "distal";
    }
    print $1, $2, $3, type, $4, $5;
}' "${DATA_DIR}/tmp_promoter_keys.txt" "${DATA_DIR}/tmp_merged_with_info.bed" >> "${OUTPUT_FILE}"

# Cleanup temporary files
echo "Cleaning up temporary files..."
rm -f "${DATA_DIR}/tmp_peaks_all.bed"
rm -f "${DATA_DIR}/tmp_merged.bed"
rm -f "${DATA_DIR}/tmp_tss_promoters.bed"
rm -f "${DATA_DIR}/tmp_promoter_peaks.bed"
rm -f "${DATA_DIR}/tmp_peaks_with_source.bed"
rm -f "${DATA_DIR}/tmp_peaks_with_source_sorted.bed"
rm -f "${DATA_DIR}/tmp_merged_with_info.bed"
rm -f "${DATA_DIR}/tmp_merged_sorted.bed"
rm -f "${DATA_DIR}/tmp_promoter_sorted.bed"
rm -f "${DATA_DIR}/tmp_promoter_overlap.bed"
rm -f "${DATA_DIR}/tmp_promoter_regions.bed"
rm -f "${DATA_DIR}/tmp_promoter_keys.txt"

# Final validation
if [[ -f "${OUTPUT_FILE}" ]]; then
    final_count=$(tail -n +2 "${OUTPUT_FILE}" | wc -l)
    promoter_final=$(grep -c "promoter" "${OUTPUT_FILE}" || echo "0")
    distal_final=$(grep -c "distal" "${OUTPUT_FILE}" || echo "0")

    echo "=========================================="
    echo "Task T008 completed successfully!"
    echo "Output file: ${OUTPUT_FILE}"
    echo "Total merged CREs: ${final_count}"
    echo "Promoter CREs: ${promoter_final}"
    echo "Distal CREs: ${distal_final}"
    echo "=========================================="
else
    echo "Error: Output file was not created."
    exit 1
fi