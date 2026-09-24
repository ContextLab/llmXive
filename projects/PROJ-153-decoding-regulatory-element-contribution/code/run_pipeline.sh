#!/bin/bash
# run_pipeline.sh: Orchestrate the full yeast CRE analysis pipeline.
# Exits on error (set -e) and logs all steps.

set -e

# Configuration
LOG_FILE="logs/pipeline.log"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

mkdir -p logs
exec > >(tee -a "$LOG_FILE") 2>&1

log() {
    echo "[$(date -Iseconds)] $1" | tee -a "$LOG_FILE"
}

log "Starting full pipeline execution..."

# Phase 1: Setup (Assumed complete, but verify)
log "Phase 1: Verifying setup..."
python code/00_verify_manifest.py --manifest data/manifest.yaml

# Phase 2: Foundational
log "Phase 2: Running foundational steps..."
bash code/01_download_data.sh
bash code/02_preprocess_chipseq.sh
bash code/03_call_peaks.sh
Rscript code/03b1_extract_top_cres.R
Rscript code/03b2_compute_intersections.R
Rscript code/03b3_calculate_overlap_stats.R
Rscript code/03c1_run_sweep_lmm_0.01.R
Rscript code/03c2_run_sweep_lmm_0.10.R
Rscript code/03c3_run_sweep_lmm_0.05.R
Rscript code/03c_extract_peak_signals.R
bash code/04_merge_annotate.sh
bash code/04b_load_hic.sh
bash code/06a_define_null_regions.sh
bash code/06b_compute_null_signal.sh
python code/05b_compute_delta_signal.py \
    --cre-signal data/processed/CRE_merged.bed \
    --null-signal data/processed/null_region_signal.bed \
    --output data/processed/delta_peak_signal.tsv
python code/01b_validate_eqtl_schema.py --eqtl data/raw/eqtl_data.tsv
python code/01_stream_eqtl.py --manifest data/manifest.yaml

# Phase 3: User Story 1
log "Phase 3: Running User Story 1 steps..."
python code/05a1_validate_motif.py --cres data/processed/CRE_merged.bed --output data/processed/motif_validation_flags.tsv
python code/05a2_validate_hic.py --cres data/processed/CRE_merged.bed --hic data/processed/hic_matrix_10kb.cool --output data/processed/hic_validation_flags.tsv
python code/05b_check_collinearity.py \
    --peak-signal data/processed/peak_signal_matrix.tsv \
    --output data/processed/vif_flags.tsv
# T013c: Compute weights
python code/05c_compute_weights.py \
    --motif-flags data/processed/motif_validation_flags.tsv \
    --hic-flags data/processed/hic_validation_flags.tsv \
    --vif-flags data/processed/vif_flags.tsv \
    --delta-signal data/processed/delta_peak_signal.tsv \
    --output data/processed/weights.tsv
Rscript code/06_fit_lmm.R --weights data/processed/weights.tsv
Rscript code/07_permutation_test.R
Rscript code/10_generate_reports.R

# Phase 5: User Story 3
log "Phase 5: Running User Story 3 steps..."
bash code/11_create_bigwig.sh
Rscript code/09_summit_match.R

# Phase N: Polish
log "Phase N: Running polish steps..."
bash code/13_final_integrity_check.sh

log "Pipeline execution completed successfully."
echo "Pipeline completed. Check results/ and data/processed/ for outputs."