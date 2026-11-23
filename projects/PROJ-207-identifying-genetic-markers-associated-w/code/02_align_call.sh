#!/bin/bash
# code/02_align_call.sh
# Aligns FASTQ files to reference genome and calls variants using FreeBayes.
# Supports both real and synthetic data inputs.
#
# Usage:
#   ./code/02_align_call.sh <input_prefix> <reference_fasta> <output_prefix>
#
# Arguments:
#   input_prefix   : Prefix for input FASTQ files (e.g., data/interim/synthetic_R1)
#                    If provided without extension, script assumes _R1.fastq and _R2.fastq
#   reference_fasta: Path to reference genome FASTA file
#   output_prefix  : Prefix for output files (e.g., data/interim/aligned)
#
# Environment Variables:
#   BWA_MEM_THREADS: Number of threads for BWA MEM (default: 4)
#   FREEBAYES_THREADS: Number of threads for FreeBayes (default: 4)
#   QUAL_THRESHOLD: Minimum variant quality (default: 30)
#   DEPTH_THRESHOLD: Minimum depth (default: 10)

set -euo pipefail

# Configuration with defaults
BWA_MEM_THREADS="${BWA_MEM_THREADS:-4}"
FREEBAYES_THREADS="${FREEBAYES_THREADS:-4}"
QUAL_THRESHOLD="${QUAL_THRESHOLD:-30}"
DEPTH_THRESHOLD="${DEPTH_THRESHOLD:-10}"

# Validate arguments
if [ $# -ne 3 ]; then
    echo "Usage: $0 <input_prefix> <reference_fasta> <output_prefix>" >&2
    echo "  input_prefix: Prefix for input FASTQ files (without _R1/_R2 suffix)" >&2
    echo "  reference_fasta: Path to reference genome FASTA" >&2
    echo "  output_prefix: Prefix for output files" >&2
    exit 1
fi

INPUT_PREFIX="$1"
REFERENCE_FASTA="$2"
OUTPUT_PREFIX="$3"

# Validate input files exist
R1_FILE="${INPUT_PREFIX}_R1.fastq"
R2_FILE="${INPUT_PREFIX}_R2.fastq"

if [ ! -f "$R1_FILE" ]; then
    echo "ERROR: R1 FASTQ file not found: $R1_FILE" >&2
    exit 1
fi

if [ ! -f "$R2_FILE" ]; then
    echo "ERROR: R2 FASTQ file not found: $R2_FILE" >&2
    exit 1
fi

if [ ! -f "$REFERENCE_FASTA" ]; then
    echo "ERROR: Reference FASTA not found: $REFERENCE_FASTA" >&2
    exit 1
fi

# Create output directory if it doesn't exist
OUTPUT_DIR=$(dirname "$OUTPUT_PREFIX")
mkdir -p "$OUTPUT_DIR"

# Index reference if not already indexed
REF_INDEX="${REFERENCE_FASTA%.fasta}.bwt"
if [ ! -f "$REF_INDEX" ]; then
    echo "Indexing reference genome: $REFERENCE_FASTA"
    bwa index "$REFERENCE_FASTA"
fi

# Alignment step
ALIGNMENT_BAM="${OUTPUT_PREFIX}.sorted.bam"
echo "Aligning reads: $R1_FILE + $R2_FILE"
bwa mem -t "$BWA_MEM_THREADS" "$REFERENCE_FASTA" "$R1_FILE" "$R2_FILE" | \
    samtools view -bS - | \
    samtools sort -@ "$BWA_MEM_THREADS" -o "$ALIGNMENT_BAM"

# Index alignment
samtools index "$ALIGNMENT_BAM"

# Variant calling with FreeBayes
VCF_OUTPUT="${OUTPUT_PREFIX}.vcf"
echo "Calling variants with FreeBayes"
freebayes \
    -f "$REFERENCE_FASTA" \
    -b "$ALIGNMENT_BAM" \
    -t "$FREEBAYES_THREADS" \
    --min-alternate-fraction 0.01 \
    --min-alternate-count 2 \
    --min-mapping-quality 20 \
    --min-base-quality 20 \
    "$VCF_OUTPUT"

# Filter variants based on quality and depth
FILTERED_VCF="${OUTPUT_PREFIX}.filtered.vcf"
echo "Filtering variants (QUAL > $QUAL_THRESHOLD, DP >= $DEPTH_THRESHOLD)"
vcffilter \
    -f "QUAL > $QUAL_THRESHOLD" \
    -f "DP >= $DEPTH_THRESHOLD" \
    "$VCF_OUTPUT" > "$FILTERED_VCF"

# Generate summary statistics
TOTAL_VARIANTS=$(grep -v "^#" "$VCF_OUTPUT" | wc -l)
FILTERED_VARIANTS=$(grep -v "^#" "$FILTERED_VCF" | wc -l)

SUMMARY_FILE="${OUTPUT_PREFIX}_summary.txt"
cat > "$SUMMARY_FILE" <<EOF
Alignment and Variant Calling Summary
=====================================
Input R1: $R1_FILE
Input R2: $R2_FILE
Reference: $REFERENCE_FASTA
Output BAM: $ALIGNMENT_BAM
Raw VCF: $VCF_OUTPUT
Filtered VCF: $FILTERED_VCF

Parameters:
  BWA Threads: $BWA_MEM_THREADS
  FreeBayes Threads: $FREEBAYES_THREADS
  Quality Threshold: $QUAL_THRESHOLD
  Depth Threshold: $DEPTH_THRESHOLD

Results:
  Total Variants: $TOTAL_VARIANTS
  Filtered Variants: $FILTERED_VARIANTS
  Variants Removed: $((TOTAL_VARIANTS - FILTERED_VARIANTS))
EOF

echo "Pipeline complete. Summary: $SUMMARY_FILE"
echo "Filtered VCF: $FILTERED_VCF"