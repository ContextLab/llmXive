#!/bin/bash
#
# run_fmriprep.sh
# Executes containerized fMRIPrep (pinned version 23.1.1) with HCP configuration.
#
# This script processes resting-state fMRI data from OpenNeuro ds004285.
# It expects pre-downloaded BIDS data in data/raw/ and outputs preprocessed
# derivatives to data/processed/fmriprep/.
#
# Usage:
#   ./code/preprocessing/run_fmriprep.sh [subject_id]
#   If subject_id is provided, only that subject is processed.
#   Otherwise, all subjects in data/raw/ are processed.
#
# Prerequisites:
#   - Docker or Singularity installed and available
#   - data/raw/ contains valid BIDS dataset (ds004285)
#   - Sufficient disk space (~100GB per subject for derivatives)
#
# Note: This script uses the HCP minimal preprocessing pipeline configuration
#       as specified in the project requirements.
#

set -euo pipefail

# Configuration
FMRIPREP_VERSION="23.1.1"
FMRIPREP_IMAGE="poldracklab/fmriprep:${FMRIPREP_VERSION}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RAW_DATA_DIR="${PROJECT_ROOT}/data/raw"
OUTPUT_DIR="${PROJECT_ROOT}/data/processed/fmriprep"
WORK_DIR="${OUTPUT_DIR}/work"
FS_LICENSE_FILE="${PROJECT_ROOT}/data/raw/freesurfer_license.txt"

# Colors for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check for Docker or Singularity
    if command -v docker &> /dev/null; then
        CONTAINER_ENGINE="docker"
        log_info "Using Docker as container engine"
    elif command -v singularity &> /dev/null; then
        CONTAINER_ENGINE="singularity"
        log_info "Using Singularity as container engine"
    else
        log_error "Neither Docker nor Singularity found. Please install one of them."
        exit 1
    fi

    # Check for BIDS data
    if [ ! -d "${RAW_DATA_DIR}" ]; then
        log_error "Raw data directory not found: ${RAW_DATA_DIR}"
        log_error "Please run code/preprocessing/download_openneuro.py first."
        exit 1
    fi

    # Check for dataset_description.json (BIDS validation)
    if [ ! -f "${RAW_DATA_DIR}/dataset_description.json" ]; then
        log_error "BIDS dataset_description.json not found in ${RAW_DATA_DIR}"
        exit 1
    fi

    # Check for FreeSurfer license (required for fMRIPrep)
    if [ ! -f "${FS_LICENSE_FILE}" ]; then
        log_warn "FreeSurfer license file not found at ${FS_LICENSE_FILE}"
        log_warn "fMRIPrep requires a FreeSurfer license for cortical surface reconstruction."
        log_warn "Please obtain a license from https://surfer.nmr.mgh.harvard.edu/registration.html"
        log_warn "Continuing without FreeSurfer license may result in limited output."
    else
        log_info "FreeSurfer license found"
    fi

    # Create output directories
    mkdir -p "${OUTPUT_DIR}"
    mkdir -p "${WORK_DIR}"

    log_info "Prerequisites check passed"
}

# Run fMRIPrep for a single subject
run_fmriprep_subject() {
    local subject_id="$1"
    local subject_dir="${RAW_DATA_DIR}/sub-${subject_id}"

    if [ ! -d "${subject_dir}" ]; then
        log_warn "Subject directory not found: ${subject_dir}. Skipping."
        return 0
    fi

    log_info "Processing subject: ${subject_id}"

    # fMRIPrep arguments with HCP configuration
    # --hcp: Use HCP minimal preprocessing pipeline
    # --fs-license-file: Path to FreeSurfer license (if available)
    # --work-dir: Working directory for intermediate files
    # --output-spaces: Output spaces (MNI152NLin2009cAsym is standard)
    # --cifti-output: Generate CIFTI dense timeseries (HCP style)
    local fmriprep_args=(
        "${RAW_DATA_DIR}"
        "${OUTPUT_DIR}"
        "participant"
        --participant-label "${subject_id}"
        --output-spaces MNI152NLin2009cAsym
        --work-dir "${WORK_DIR}/sub-${subject_id}"
        --fs-no-reconall  # Skip recon-all if license is missing or to speed up
        --omp-nthreads 4
        --nprocs 4
        --mem_mb 8000
        --stop-on-first-crash
    )

    # Add HCP-specific flags if available
    if [ -f "${FS_LICENSE_FILE}" ]; then
        fmriprep_args+=(--fs-license-file "${FS_LICENSE_FILE}")
    fi

    # Add CIFTI output for HCP-style dense timeseries
    fmriprep_args+=(--cifti-output 91k)

    log_info "Running fMRIPrep with args: ${fmriprep_args[*]}"

    if [ "${CONTAINER_ENGINE}" = "docker" ]; then
        docker run --rm -it \
            -v "${RAW_DATA_DIR}":/data:ro \
            -v "${OUTPUT_DIR}":/out \
            -v "${WORK_DIR}":/work \
            ${FMRIPREP_IMAGE} \
            /data /out participant "${fmriprep_args[@]:3}"
    else
        # Singularity version
        singularity run --cleanenv \
            -B "${RAW_DATA_DIR}:/data:ro" \
            -B "${OUTPUT_DIR}:/out" \
            -B "${WORK_DIR}:/work" \
            "${FMRIPREP_IMAGE}" \
            /data /out participant "${fmriprep_args[@]:3}"
    fi

    log_info "Completed subject: ${subject_id}"
}

# Main execution
main() {
    check_prerequisites

    local subject_arg="${1:-}"

    if [ -n "${subject_arg}" ]; then
        # Process single subject
        run_fmriprep_subject "${subject_arg}"
    else
        # Process all subjects
        log_info "Discovering subjects in ${RAW_DATA_DIR}..."
        
        # Find all subject directories matching BIDS pattern
        local subjects=()
        for dir in "${RAW_DATA_DIR}"/sub-*; do
            if [ -d "${dir}" ]; then
                local subj_id=$(basename "${dir}" | sed 's/^sub-//')
                subjects+=("${subj_id}")
            fi
        done

        if [ ${#subjects[@]} -eq 0 ]; then
            log_error "No subjects found in ${RAW_DATA_DIR}"
            exit 1
        fi

        log_info "Found ${#subjects[@]} subjects: ${subjects[*]}"

        for subject_id in "${subjects[@]}"; do
            run_fmriprep_subject "${subject_id}"
        done
    fi

    log_info "fMRIPrep pipeline completed successfully"
}

main "$@"
