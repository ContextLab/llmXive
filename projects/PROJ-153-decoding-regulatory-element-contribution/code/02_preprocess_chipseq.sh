#!/bin/bash
#
# code/02_preprocess_chipseq.sh
# Purpose: Adapter trimming (fastp) and alignment (bowtie2) for ChIP-seq data.
# Constraints: 
#   - Max 2 threads per job
#   - MAPQ >= 30 for alignment filtering
#   - Abort if input files missing or tools unavailable
#
# Input: 
#   - data/raw/fastq/*.fastq.gz (from T005)
#   - data/reference/genome.fa (from plan.md setup)
#   - data/reference/genome.1.bt2 ... (bowtie2 index)
#
# Output:
#   - data/processed/fastq/*.clean.fastq.gz (trimmed)
#   - data/processed/bam/*.aligned.bam (sorted, indexed, filtered)
#   - logs/preprocess/*.log
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RAW_DIR="$PROJECT_ROOT/data/raw/fastq"
REF_DIR="$PROJECT_ROOT/data/reference"
PROC_DIR="$PROJECT_ROOT/data/processed"
LOG_DIR="$PROJECT_ROOT/logs/preprocess"
THREADS=2
MIN_MAPQ=30

# Paths
FASTQ_INPUT_DIR="$RAW_DIR"
OUTPUT_FASTQ_DIR="$PROC_DIR/fastq"
OUTPUT_BAM_DIR="$PROC_DIR/bam"
BOWT2_INDEX="$REF_DIR/genome"

# Ensure tools are available
if ! command -v fastp &> /dev/null; then
    echo "ERROR: fastp not found. Please install fastp (conda install -c bioconda fastp)."
    exit 1
fi
if ! command -v bowtie2 &> /dev/null; then
    echo "ERROR: bowtie2 not found. Please install bowtie2 (conda install -c bioconda bowtie2)."
    exit 1
fi
if ! command -v samtools &> /dev/null; then
    echo "ERROR: samtools not found. Please install samtools (conda install -c bioconda samtools)."
    exit 1
fi

# Create output directories
mkdir -p "$OUTPUT_FASTQ_DIR" "$OUTPUT_BAM_DIR" "$LOG_DIR"

# Verify reference index exists
if [[ ! -f "$BOWT2_INDEX.1.bt2" ]]; then
    echo "ERROR: Bowtie2 index not found at $BOWT2_INDEX.1.bt2. Run T002/T005 to prepare reference."
    exit 1
fi

# Find input files
FASTQ_FILES=("$FASTQ_INPUT_DIR"/*.fastq.gz)
if [[ ! -e "${FASTQ_FILES[0]}" ]]; then
    echo "ERROR: No FASTQ files found in $FASTQ_INPUT_DIR. Ensure T005 has completed successfully."
    exit 1
fi

echo "Starting preprocessing for ${#FASTQ_FILES[@]} files..."
echo "Threads: $THREADS, Min MAPQ: $MIN_MAPQ"

for fastq in "${FASTQ_FILES[@]}"; do
    base=$(basename "$fastq" .fastq.gz)
    echo "Processing: $base"
    
    # Define output paths
    clean_fastq="$OUTPUT_FASTQ_DIR/${base}.clean.fastq.gz"
    log_file="$LOG_DIR/${base}_preprocess.log"
    align_bam="$OUTPUT_BAM_DIR/${base}.aligned.bam"
    sort_bam="$OUTPUT_BAM_DIR/${base}.aligned.sorted.bam"
    
    # 1. Adapter Trimming with fastp
    # -i: input, -o: output, -h/-j: HTML/JSON reports
    echo "Running fastp for $base..."
    fastp \
        -i "$fastq" \
        -o "$clean_fastq" \
        -h "$LOG_DIR/${base}_fastp.html" \
        -j "$LOG_DIR/${base}_fastp.json" \
        -w "$THREADS" \
        --thread_limit "$THREADS" \
        --detect_adapter_for_pe \
        --length_required 30 \
        2>&1 | tee "$log_file"

    if [[ ! -s "$clean_fastq" ]]; then
        echo "ERROR: fastp produced empty output for $base. Check logs."
        exit 1
    fi

    # 2. Alignment with bowtie2
    # -p: threads, -x: index, -U: unpaired input
    # --no-unal: suppress unaligned output
    echo "Aligning $base with bowtie2..."
    bowtie2 \
        -p "$THREADS" \
        -x "$BOWT2_INDEX" \
        -U "$clean_fastq" \
        --no-unal \
        -S "$align_bam.sam" \
        2>> "$log_file"

    # Convert SAM to BAM, sort, and filter by MAPQ
    echo "Sorting and filtering alignments (MAPQ >= $MIN_MAPQ)..."
    samtools view -b -q "$MIN_MAPQ" "$align_bam.sam" | \
        samtools sort -@ "$THREADS" -o "$sort_bam"
    
    # Index the sorted BAM
    samtools index "$sort_bam"

    # Cleanup intermediate SAM
    rm -f "$align_bam.sam"

    echo "Completed: $base -> $sort_bam"
done

echo "All preprocessing tasks completed successfully."