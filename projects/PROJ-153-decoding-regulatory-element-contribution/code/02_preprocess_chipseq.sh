#!/bin/bash
# T006: Preprocess ChIP-seq data
# Performs adapter trimming with fastp and alignment with bowtie2
# Constraints: ≤2 threads, MAPQ ≥ 30
# Dependencies: fastp, bowtie2, samtools
# Input: Manifest with verified accessions (T003) and downloaded FASTQ (T005)
# Output: Aligned, filtered BAM files in data/processed/

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"
PROCESSED_DIR="$PROJECT_ROOT/data/processed"
LOG_DIR="$PROJECT_ROOT/logs"
MANIFEST_FILE="$DATA_DIR/manifest.yaml"
REF_GENOME="yeast_s288c" # Assumes bowtie2 index is built and available as 'yeast_s288c'

# Create output directories
mkdir -p "$PROCESSED_DIR"
mkdir -p "$LOG_DIR"

# Logging function
log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" | tee -a "$LOG_DIR/preprocess_chipseq.log"
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    command -v fastp >/dev/null 2>&1 || { log "ERROR: fastp not found"; exit 1; }
    command -v bowtie2 >/dev/null 2>&1 || { log "ERROR: bowtie2 not found"; exit 1; }
    command -v samtools >/dev/null 2>&1 || { log "ERROR: samtools not found"; exit 1; }
    log "All dependencies found."
}

# Parse manifest and process samples
process_manifest() {
    if [[ ! -f "$MANIFEST_FILE" ]]; then
        log "ERROR: Manifest file not found: $MANIFEST_FILE"
        exit 1
    fi

    log "Processing manifest: $MANIFEST_FILE"

    # Extract ChIP-seq entries from YAML using grep/awk (simple parsing for this task)
    # Assumes format: - accession: GSE12345, type: ChIP-seq, condition: heatshock, tf: Msn2
    # This is a simplified parser; a robust solution would use a YAML parser in Python
    
    # We will iterate through lines looking for ChIP-seq entries
    local current_accession=""
    local current_type=""
    local current_condition=""
    local current_tf=""
    local current_fastq=""

    while IFS= read -r line; do
        # Simple state machine to parse YAML-like structure
        if [[ "$line" =~ ^[[:space:]]*-[[:space:]]*accession:[[:space:]]*(.*) ]]; then
            current_accession="${BASH_REMATCH[1]}"
        elif [[ "$line" =~ ^[[:space:]]*type:[[:space:]]*(.*) ]]; then
            current_type="${BASH_REMATCH[1]}"
        elif [[ "$line" =~ ^[[:space:]]*condition:[[:space:]]*(.*) ]]; then
            current_condition="${BASH_REMATCH[1]}"
        elif [[ "$line" =~ ^[[:space:]]*tf:[[:space:]]*(.*) ]]; then
            current_tf="${BASH_REMATCH[1]}"
        elif [[ "$line" =~ ^[[:space:]]*fastq:[[:space:]]*(.*) ]]; then
            current_fastq="${BASH_REMATCH[1]}"
        fi

        # Process if we have a complete ChIP-seq entry
        if [[ -n "$current_accession" && "$current_type" == "ChIP-seq" && -n "$current_fastq" ]]; then
            if [[ -f "$current_fastq" ]]; then
                log "Processing ChIP-seq sample: $current_accession ($current_tf - $current_condition)"
                run_pipeline "$current_accession" "$current_tf" "$current_condition" "$current_fastq"
            else
                log "WARNING: FASTQ file not found for $current_accession: $current_fastq"
            fi

            # Reset state
            current_accession=""
            current_type=""
            current_condition=""
            current_tf=""
            current_fastq=""
        fi
    done < "$MANIFEST_FILE"
}

# Run the pipeline for a single sample
run_pipeline() {
    local accession=$1
    local tf=$2
    local condition=$3
    local input_fastq=$4

    # Define output paths
    local sample_id="${accession}_${tf}_${condition}"
    local trimmed_fastq="$PROCESSED_DIR/${sample_id}_trimmed.fastq.gz"
    local aligned_bam="$PROCESSED_DIR/${sample_id}.bam"
    local sorted_bam="$PROCESSED_DIR/${sample_id}_sorted.bam"
    local filtered_bam="$PROCESSED_DIR/${sample_id}_filtered.bam"

    log "Step 1: Adapter trimming with fastp"
    # fastp: adapter trimming, quality filtering, output gzipped FASTQ
    # -i: input, -o: output, -j: json report, -h: html report
    # --thread: 2 (constraint)
    fastp \
        -i "$input_fastq" \
        -o "$trimmed_fastq" \
        -j "$LOG_DIR/${sample_id}_fastp.json" \
        -h "$LOG_DIR/${sample_id}_fastp.html" \
        --thread 2 \
        --qualified_quality_phred 20 \
        --length_required 36 \
        --n_base_limit 5 \
        --compression 6 \
        2>> "$LOG_DIR/preprocess_chipseq.log"

    if [[ ! -f "$trimmed_fastq" ]]; then
        log "ERROR: fastp failed to produce output for $sample_id"
        exit 1
    fi

    log "Step 2: Alignment with bowtie2"
    # bowtie2: alignment to yeast genome
    # -p: threads (constraint: ≤2)
    # -x: genome index
    # -U: unpaired input (trimmed FASTQ)
    # -S: output SAM
    # --very-sensitive: standard for ChIP-seq
    bowtie2 \
        -p 2 \
        -x "$REF_GENOME" \
        -U "$trimmed_fastq" \
        -S "$LOG_DIR/${sample_id}.sam" \
        --very-sensitive \
        2>> "$LOG_DIR/preprocess_chipseq.log"

    if [[ ! -f "$LOG_DIR/${sample_id}.sam" ]]; then
        log "ERROR: bowtie2 failed to produce output for $sample_id"
        exit 1
    fi

    log "Step 3: Convert SAM to BAM and sort"
    samtools view -bS "$LOG_DIR/${sample_id}.sam" | \
        samtools sort -@ 2 -o "$sorted_bam" -

    if [[ ! -f "$sorted_bam" ]]; then
        log "ERROR: samtools sort failed for $sample_id"
        exit 1
    fi

    log "Step 4: Filter for MAPQ ≥ 30"
    # samtools view -q 30: keep alignments with MAPQ >= 30
    # -b: output BAM
    samtools view -b -q 30 "$sorted_bam" > "$filtered_bam"

    # Index the final BAM
    samtools index "$filtered_bam"

    # Cleanup intermediate files
    rm -f "$LOG_DIR/${sample_id}.sam"
    rm -f "$trimmed_fastq" # Keep trimmed fastq? Usually yes, but task focuses on BAM. 
    # Let's keep the trimmed fastq for reproducibility if needed, but the task emphasizes the BAM.
    # Re-reading task: "output peak counts" later, so BAM is key. We'll keep trimmed fastq as intermediate.
    
    # Actually, let's keep the trimmed fastq as it's useful.
    # But the primary output is the filtered BAM.
    
    # Verify output
    if [[ -f "$filtered_bam" && -f "${filtered_bam}.bai" ]]; then
        local read_count=$(samtools view -c "$filtered_bam")
        log "SUCCESS: Processed $sample_id. Filtered BAM: $filtered_bam ($read_count reads)"
    else
        log "ERROR: Final BAM or index missing for $sample_id"
        exit 1
    fi
}

# Main execution
main() {
    log "Starting ChIP-seq preprocessing pipeline (T006)"
    check_dependencies
    process_manifest
    log "Pipeline completed successfully."
}

main "$@"
