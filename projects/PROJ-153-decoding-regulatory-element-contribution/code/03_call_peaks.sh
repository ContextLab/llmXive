#!/bin/bash
#
# code/03_call_peaks.sh
# Purpose: Run MACS2 callpeak on preprocessed BAM files with an FDR sweep.
# Input:   BAM files in data/processed/<sample_id>/
# Output:  Peak files and a summary count table in data/processed/peaks/
#
# FDR thresholds to test: 0.01, 0.05, 0.10
# Constraint: Do NOT calculate top-20 CRE overlap here (that belongs to T041).
#

set -euo pipefail

# Configuration
INPUT_DIR="data/processed"
OUTPUT_DIR="data/processed/peaks"
FDR_THRESHOLDS=(0.01 0.05 0.10)
THREADS=2
GENOME="saccharomyces_cerevisiae" # MACS2 built-in genome name or custom
# Note: MACS2 uses --qvalue for FDR. We will sweep this parameter.

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Initialize summary file
SUMMARY_FILE="${OUTPUT_DIR}/peak_counts_summary.tsv"
echo -e "sample_id\tfdr_threshold\tpeak_count" > "${SUMMARY_FILE}"

# Find all input BAM files
# Expected structure: data/processed/<sample_id>/<sample_id>_aligned.bam
echo "Scanning for BAM files in ${INPUT_DIR}..."
BAM_FILES=$(find "${INPUT_DIR}" -name "*_aligned.bam" -type f)

if [ -z "${BAM_FILES}" ]; then
    echo "ERROR: No BAM files found in ${INPUT_DIR}. Ensure T006 (preprocessing) has completed."
    exit 1
fi

# Process each BAM file
for BAM_PATH in ${BAM_FILES}; do
    SAMPLE_ID=$(basename "${BAM_PATH}" | sed 's/_aligned.bam$//')
    SAMPLE_DIR="${INPUT_DIR}/${SAMPLE_ID}"
    OUTPUT_SAMPLE_DIR="${OUTPUT_DIR}/${SAMPLE_ID}"
    
    echo "----------------------------------------"
    echo "Processing Sample: ${SAMPLE_ID}"
    echo "Input BAM: ${BAM_PATH}"
    echo "----------------------------------------"

    mkdir -p "${OUTPUT_SAMPLE_DIR}"

    # Run MACS2 for each FDR threshold
    for FDR in "${FDR_THRESHOLDS[@]}"; do
        OUTPUT_PREFIX="${OUTPUT_SAMPLE_DIR}/${SAMPLE_ID}_FDR${FDR}"
        
        echo "  Running MACS2 with q-value cutoff: ${FDR}..."
        
        # MACS2 callpeak
        # --nomodel: recommended for ChIP-exo or when model building fails, 
        #            but standard ChIP-seq usually uses default. 
        #            Given T006 constraints (MAPQ>=30), we assume standard peaks.
        # --extsize: If --nomodel is used, we need extension size. 
        #            Default is 200bp. Let's stick to defaults unless specified.
        # --keep-dup: auto (default)
        
        macs2 callpeak \
            -t "${BAM_PATH}" \
            -f BAM \
            -g "${GENOME}" \
            -n "${OUTPUT_PREFIX}" \
            --outdir "${OUTPUT_SAMPLE_DIR}" \
            --qvalue "${FDR}" \
            --keep-dup auto \
            -B \
            --SPMR \
            --threads "${THREADS}" \
            2>> "${OUTPUT_PREFIX}.log"

        if [ $? -ne 0 ]; then
            echo "  ERROR: MACS2 failed for ${SAMPLE_ID} at FDR ${FDR}. Check ${OUTPUT_PREFIX}.log"
            exit 1
        fi

        # Count peaks (excluding header lines starting with #)
        # MACS2 outputs .narrowPeak file
        PEAK_FILE="${OUTPUT_SAMPLE_DIR}/${SAMPLE_ID}_FDR${FDR}_peaks.narrowPeak"
        
        if [ -f "${PEAK_FILE}" ]; then
            COUNT=$(grep -v "^#" "${PEAK_FILE}" | wc -l)
            echo "    -> Found ${COUNT} peaks."
            echo -e "${SAMPLE_ID}\t${FDR}\t${COUNT}" >> "${SUMMARY_FILE}"
        else
            echo "    -> WARNING: Peak file not generated for FDR ${FDR}."
            echo -e "${SAMPLE_ID}\t${FDR}\t0" >> "${SUMMARY_FILE}"
        fi
    done
done

echo "----------------------------------------"
echo "Peak calling complete."
echo "Summary saved to: ${SUMMARY_FILE}"
echo "----------------------------------------"
cat "${SUMMARY_FILE}"

exit 0
