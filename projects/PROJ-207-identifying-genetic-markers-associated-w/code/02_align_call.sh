#!/bin/bash
# code/02_align_call.sh
# Aligns FASTQ files to reference genome and calls variants using FreeBayes.
# Supports parallel processing for I/O bound alignment steps if profile indicates bottleneck.
#
# Usage:
#   ./code/02_align_call.sh [--input <fastq_pattern>] [--output-dir <dir>] [--threads <N>]
#
# Input:
#   - data/interim/real_*.fastq or data/interim/synthetic_*.fastq (R1/R2 pairs)
#   - data/interim/reference.fasta (must exist)
#
# Output:
#   - data/interim/*.bam (sorted, indexed)
#   - data/interim/variants.vcf (merged)

set -euo pipefail

# Configuration
INPUT_PATTERN="${1:-data/interim/*_R1.fastq}"
OUTPUT_DIR="${2:-data/interim}"
THREADS="${3:-4}"
REFERENCE="data/interim/reference.fasta"
QUAL_THRESHOLD=30
MIN_DEPTH=10

# Check dependencies
for cmd in bwa freebayes samtools; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "ERROR: Required command '$cmd' not found. Please install it." >&2
        exit 1
    fi
done

if [[ ! -f "$REFERENCE" ]]; then
    echo "ERROR: Reference genome not found at $REFERENCE" >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

# Check if parallel processing is beneficial (simulated profile check)
# In a real scenario, this would read from data/processed/profile_report.txt
# For now, we assume parallel is enabled if THREADS > 1
USE_PARALLEL=false
if [[ $THREADS -gt 1 ]]; then
    USE_PARALLEL=true
    echo "INFO: Parallel processing enabled with $THREADS threads."
else
    echo "INFO: Single-threaded mode."
fi

# Find R1/R2 pairs
declare -a R1_FILES
declare -a R2_FILES
declare -a SAMPLE_NAMES

for r1_file in $INPUT_PATTERN; do
    if [[ ! -f "$r1_file" ]]; then
        continue
    fi
    sample_name=$(basename "$r1_file" _R1.fastq)
    r2_file="${r1_file/_R1.fastq/_R2.fastq}"
    
    if [[ ! -f "$r2_file" ]]; then
        echo "WARNING: R2 file missing for $r1_file, skipping." >&2
        continue
    fi

    R1_FILES+=("$r1_file")
    R2_FILES+=("$r2_file")
    SAMPLE_NAMES+=("$sample_name")
done

if [[ ${#R1_FILES[@]} -eq 0 ]]; then
    echo "ERROR: No valid FASTQ pairs found matching pattern: $INPUT_PATTERN" >&2
    exit 1
fi

echo "INFO: Found ${#R1_FILES[@]} sample pairs to process."

# Function to process a single sample
process_sample() {
    local r1=$1
    local r2=$2
    local sample=$3
    local out_bam="$OUTPUT_DIR/${sample}.bam"
    
    echo "INFO: Processing sample: $sample"
    
    # Alignment
    bwa mem -t "$THREADS" "$REFERENCE" "$r1" "$r2" | \
        samtools view -bS - | \
        samtools sort -@ "$THREADS" -o "$out_bam"
    
    # Index
    samtools index "$out_bam"
    
    # Variant calling
    local out_vcf="$OUTPUT_DIR/${sample}_raw.vcf"
    freebayes -f "$REFERENCE" -p 1 --min-alternate-fraction 0.05 \
        --min-alternate-count 2 --min-coverage "$MIN_DEPTH" \
        "$out_bam" > "$out_vcf"
    
    # Filter by quality
    local out_filtered_vcf="$OUTPUT_DIR/${sample}.vcf"
    awk -v q="$QUAL_THRESHOLD" '
        /^#/ { print; next }
        $5 > q { print }
    ' "$out_vcf" > "$out_filtered_vcf"
    
    echo "INFO: Finished sample: $sample"
}

export -f process_sample
export REFERENCE QUAL_THRESHOLD MIN_DEPTH THREADS OUTPUT_DIR

if [[ "$USE_PARALLEL" == true ]]; then
    echo "INFO: Starting parallel alignment and variant calling..."
    # Use GNU parallel if available, otherwise fallback to sequential
    if command -v parallel &> /dev/null; then
        printf "%s\t%s\t%s\n" "${R1_FILES[@]}" "${R2_FILES[@]}" "${SAMPLE_NAMES[@]}" | \
            parallel -j "$THREADS" --colsep '\t' process_sample {1} {2} {3}
    else
        echo "WARNING: GNU parallel not found. Falling back to sequential processing."
        for i in "${!R1_FILES[@]}"; do
            process_sample "${R1_FILES[$i]}" "${R2_FILES[$i]}" "${SAMPLE_NAMES[$i]}"
        done
    fi
else
    echo "INFO: Starting sequential alignment and variant calling..."
    for i in "${!R1_FILES[@]}"; do
        process_sample "${R1_FILES[$i]}" "${R2_FILES[$i]}" "${SAMPLE_NAMES[$i]}"
    done
fi

# Merge VCFs
echo "INFO: Merging VCF files..."
MERGED_VCF="$OUTPUT_DIR/variants_merged.vcf"
> "$MERGED_VCF"

# Write header from first VCF
first=true
for vcf in "$OUTPUT_DIR"/*.vcf; do
    if [[ -f "$vcf" ]]; then
        if [[ "$first" == true ]]; then
            grep "^#" "$vcf" >> "$MERGED_VCF"
            first=false
        fi
        grep -v "^#" "$vcf" >> "$MERGED_VCF"
    fi
done

# Sort the merged VCF
if command -v bcftools &> /dev/null; then
    bcftools sort "$MERGED_VCF" -Oz -o "${MERGED_VCF%.vcf}.vcf.gz"
    tabix -p vcf "${MERGED_VCF%.vcf}.vcf.gz"
    echo "INFO: Final sorted VCF: ${MERGED_VCF%.vcf}.vcf.gz"
else
    # Fallback if bcftools not available
    sort -k1,1 -k2,2n "$MERGED_VCF" > "${MERGED_VCF%.vcf}_sorted.vcf"
    echo "INFO: Final sorted VCF (uncompressed): ${MERGED_VCF%.vcf}_sorted.vcf"
fi

echo "INFO: Pipeline completed successfully."