#!/bin/bash
# fMRIPrep Execution Script with CPU-Limited Settings
# PROJ-103: Assessing the Impact of Mindfulness Training on Default Mode Network Activity
#
# This script runs fMRIPrep with resource constraints suitable for:
#   - GitHub Actions free tier (2 cores, 4GB RAM)
#   - Local development with limited hardware
#   - CI/CD pipelines with resource budgets
#
# Usage:
#   bash docker/run_fmriprep.sh <bids_dir> <output_dir> [participant_label]
#
# Example:
#   bash docker/run_fmriprep.sh ./data/raw ./data/processed sub-01
#
# Environment Variables (optional):
#   FMRIPREP_CPUS=2        Number of CPU cores (default: 2)
#   FMRIPREP_MEMORY=4096   Memory in MB (default: 4096)
#   FMRIPREP_WORK_DIR=./data/work   Working directory (default: ./data/work)

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

# Default resource constraints (GitHub Actions free tier compatible)
FMRIPREP_CPUS="${FMRIPREP_CPUS:-2}"
FMRIPREP_MEMORY="${FMRIPREP_MEMORY:-4096}"
FMRIPREP_WORK_DIR="${FMRIPREP_WORK_DIR:-./data/work}"

# fMRIPrep specific settings
FMRIPREP_NPROCS="${FMRIPREP_NPROCS:-2}"
FMRIPREP_OMP_NTHREADS="${FMRIPREP_OMP_NTHREADS:-1}"
FMRIPREP_LOW_MEM="${FMRIPREP_LOW_MEM:-true}"

# Docker image
FMRIPREP_IMAGE="fmriprep-mindfulness:latest"

# =============================================================================
# VALIDATION
# =============================================================================

if [ $# -lt 2 ]; then
    echo "Usage: $0 <bids_dir> <output_dir> [participant_label]"
    echo ""
    echo "Example:"
    echo "  $0 ./data/raw ./data/processed sub-01"
    echo ""
    echo "Environment variables:"
    echo "  FMRIPREP_CPUS=${FMRIPREP_CPUS}"
    echo "  FMRIPREP_MEMORY=${FMRIPREP_MEMORY}MB"
    exit 1
fi

BIDS_DIR="$1"
OUTPUT_DIR="$2"
PARTICIPANT_LABEL="${3:-}"

# Validate BIDS directory
if [ ! -d "${BIDS_DIR}" ]; then
    echo "ERROR: BIDS directory does not exist: ${BIDS_DIR}"
    exit 1
fi

# Create output and work directories
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${FMRIPREP_WORK_DIR}"

# =============================================================================
# RESOURCE CONSTRAINT VALIDATION
# =============================================================================

echo "========================================"
echo "fMRIPrep Resource Configuration"
echo "========================================"
echo "CPU Cores: ${FMRIPREP_CPUS}"
echo "Memory: ${FMRIPREP_MEMORY}MB"
echo "Work Directory: ${FMRIPREP_WORK_DIR}"
echo "BIDS Directory: ${BIDS_DIR}"
echo "Output Directory: ${OUTPUT_DIR}"
echo "Low Memory Mode: ${FMRIPREP_LOW_MEM}"
echo "========================================"

# =============================================================================
# DOCKER RUN COMMAND
# =============================================================================

echo ""
echo "Starting fMRIPrep with constrained resources..."
echo ""

# Build the docker run command with resource limits
DOCKER_CMD="docker run --rm"

# CPU constraints
DOCKER_CMD="${DOCKER_CMD} --cpus=${FMRIPREP_CPUS}"
DOCKER_CMD="${DOCKER_CMD} --cpuset-cpus=0-$((FMRIPREP_CPUS-1))"

# Memory constraints
DOCKER_CMD="${DOCKER_CMD} --memory=${FMRIPREP_MEMORY}m"
DOCKER_CMD="${DOCKER_CMD} --memory-swap=${FMRIPREP_MEMORY}m"

# Shared memory (required for multiprocessing)
DOCKER_CMD="${DOCKER_CMD} --shm-size=2g"

# Environment variables for thread control
DOCKER_CMD="${DOCKER_CMD} -e OMP_NUM_THREADS=1"
DOCKER_CMD="${DOCKER_CMD} -e OPENBLAS_NUM_THREADS=1"
DOCKER_CMD="${DOCKER_CMD} -e MKL_NUM_THREADS=1"
DOCKER_CMD="${DOCKER_CMD} -e NUMEXPR_NUM_THREADS=1"
DOCKER_CMD="${DOCKER_CMD} -e VECLIB_MAXIMUM_THREADS=1"
DOCKER_CMD="${DOCKER_CMD} -e NUMBA_NUM_THREADS=1"

# Volume mounts
DOCKER_CMD="${DOCKER_CMD} -v ${BIDS_DIR}:/data:ro"
DOCKER_CMD="${DOCKER_CMD} -v ${OUTPUT_DIR}:/output"
DOCKER_CMD="${DOCKER_CMD} -v ${FMRIPREP_WORK_DIR}:/work"

# fMRIPrep arguments
DOCKER_CMD="${DOCKER_CMD} ${FMRIPREP_IMAGE}"
DOCKER_CMD="${DOCKER_CMD} /data /output participant"

# Add participant label if specified
if [ -n "${PARTICIPANT_LABEL}" ]; then
    DOCKER_CMD="${DOCKER_CMD} --participant-label ${PARTICIPANT_LABEL}"
fi

# fMRIPrep resource constraints
DOCKER_CMD="${DOCKER_CMD} --nprocs=${FMRIPREP_NPROCS}"
DOCKER_CMD="${DOCKER_CMD} --omp-nthreads=${FMRIPREP_OMP_NTHREADS}"
DOCKER_CMD="${DOCKER_CMD} --mem-mb=${FMRIPREP_MEMORY}"

# Low memory mode (reduces parallelization, increases disk I/O)
if [ "${FMRIPREP_LOW_MEM}" = "true" ]; then
    DOCKER_CMD="${DOCKER_CMD} --low-mem"
fi

# Additional options for CI/CD
DOCKER_CMD="${DOCKER_CMD} --notrack"

# =============================================================================
# EXECUTION
# =============================================================================

echo "Executing:"
echo "${DOCKER_CMD}"
echo ""

# Execute and capture exit code
set +e
eval "${DOCKER_CMD}"
EXIT_CODE=$?
set -e

# =============================================================================
# POST-EXECUTION
# =============================================================================

echo ""
echo "========================================"
echo "fMRIPrep Execution Complete"
echo "========================================"
echo "Exit Code: ${EXIT_CODE}"
echo "Output Directory: ${OUTPUT_DIR}"
echo ""

if [ ${EXIT_CODE} -eq 0 ]; then
    echo "SUCCESS: fMRIPrep completed successfully"

    # Verify output exists
    if [ -d "${OUTPUT_DIR}/sub-*/func" ]; then
        echo "Preprocessed BOLD files found in output directory"
    else
        echo "WARNING: Expected output structure not found"
    fi
else
    echo "ERROR: fMRIPrep failed with exit code ${EXIT_CODE}"
    echo "Check logs in: ${OUTPUT_DIR}/logs/"
fi

exit ${EXIT_CODE}