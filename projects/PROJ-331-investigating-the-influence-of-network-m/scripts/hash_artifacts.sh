#!/bin/bash
# scripts/hash_artifacts.sh
# Finalizes versioning by generating SHA256 checksums for all processed artifacts
# and updating the state tracking YAML file.
#
# Prerequisites:
#   - data/processed/ directory exists with .npy, .json, .csv files
#   - results/ directory exists with .json, .pdf files
#   - state/ directory exists
#
# Output:
#   - state/artifact_checksums.yaml: Updated manifest with latest hashes and timestamps

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROCESSED_DIR="${PROJECT_ROOT}/data/processed"
RESULTS_DIR="${PROJECT_ROOT}/results"
STATE_DIR="${PROJECT_ROOT}/state"
CHECKSUMS_FILE="${STATE_DIR}/artifact_checksums.yaml"
PIPELINE_LOG="${PROJECT_ROOT}/data/logs/pipeline.log"

# Ensure directories exist
mkdir -p "${STATE_DIR}"
mkdir -p "${PROJECT_ROOT}/data/logs"

# Initialize log if missing
if [ ! -f "${PIPELINE_LOG}" ]; then
    touch "${PIPELINE_LOG}"
fi

log_msg() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [HASH_SCRIPT] $1"
    echo "${msg}" | tee -a "${PIPELINE_LOG}"
}

log_msg "Starting artifact hashing process..."

# Check if source directories have content
if [ ! -d "${PROCESSED_DIR}" ] || [ -z "$(ls -A ${PROCESSED_DIR} 2>/dev/null)" ]; then
    log_msg "WARNING: ${PROCESSED_DIR} is empty or missing. No files to hash."
fi

if [ ! -d "${RESULTS_DIR}" ] || [ -z "$(ls -A ${RESULTS_DIR} 2>/dev/null)" ]; then
    log_msg "WARNING: ${RESULTS_DIR} is empty or missing. No files to hash."
fi

# Start YAML content
YAML_CONTENT="# Artifact Checksums Manifest\n"
YAML_CONTENT+="# Generated: $(date -Iseconds)\n"
YAML_CONTENT+="# Project: PROJ-331-investigating-the-influence-of-network-m\n"
YAML_CONTENT+="# Task: T042 - Finalize versioning\n"
YAML_CONTENT+="artifacts:\n"

# Function to hash a file and append to YAML
hash_file() {
    local file_path="$1"
    local relative_path="${file_path#${PROJECT_ROOT}/}"
    
    if [ -f "${file_path}" ]; then
        local hash=$(sha256sum "${file_path}" | awk '{print $1}')
        local size=$(stat -f%z "${file_path}" 2>/dev/null || stat -c%s "${file_path}" 2>/dev/null || echo "0")
        local timestamp=$(date -Iseconds)
        
        YAML_CONTENT+="  - path: ${relative_path}\n"
        YAML_CONTENT+="    sha256: ${hash}\n"
        YAML_CONTENT+="    size_bytes: ${size}\n"
        YAML_CONTENT+="    timestamp: ${timestamp}\n"
        
        log_msg "Hashed: ${relative_path} -> ${hash:0:12}..."
    fi
}

# Hash processed data files
if [ -d "${PROCESSED_DIR}" ]; then
    for file in "${PROCESSED_DIR}"/*.{npy,json,csv} 2>/dev/null; do
        if [ -f "${file}" ]; then
            hash_file "${file}"
        fi
    done
fi

# Hash results files
if [ -d "${RESULTS_DIR}" ]; then
    for file in "${RESULTS_DIR}"/*.{json,pdf,csv} 2>/dev/null; do
        if [ -f "${file}" ]; then
            hash_file "${file}"
        fi
    done
fi

# Write to state file
echo -e "${YAML_CONTENT}" > "${CHECKSUMS_FILE}"

log_msg "Checksums written to ${CHECKSUMS_FILE}"
log_msg "Artifact hashing process completed successfully."

# Final summary
total_files=$(grep -c "path:" "${CHECKSUMS_FILE}" || echo "0")
log_msg "Total artifacts versioned: ${total_files}"

exit 0
