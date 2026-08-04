#!/bin/bash
# T051: Generate Reproducibility Package
# Bundles all raw data, processed artifacts, configuration files, and final results
# into a single tarball with a manifest checksum.
# Serves Constitution Principle I (Reproducibility) and V (Documentation).

set -euo pipefail

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PACKAGE_NAME="repro_package_${TIMESTAMP}"
OUTPUT_DIR="${PROJECT_ROOT}/data/repro_packages"
MANIFEST_FILE="${OUTPUT_DIR}/${PACKAGE_NAME}_manifest.txt"
CHECKSUM_FILE="${OUTPUT_DIR}/${PACKAGE_NAME}_checksums.txt"
TAR_FILE="${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz"

# Ensure output directory exists
mkdir -p "${OUTPUT_DIR}"

echo "=== Generating Reproducibility Package ==="
echo "Timestamp: ${TIMESTAMP}"
echo "Output Directory: ${OUTPUT_DIR}"

# Define directories and files to include
# Raw Data (BEIR downloads if present, otherwise just the structure)
RAW_DATA_DIRS=(
  "beir_data"
)

# Processed Artifacts
PROCESSED_DIRS=(
  "data/processed"
)

# Results
RESULTS_DIRS=(
  "data/results"
)

# Configuration and Code Artifacts
CONFIG_FILES=(
  "code/config.py"
  "code/requirements.txt"
)

# Documentation
DOCS_FILES=(
  "README.md"
  "docs/quickstart.md"
  "docs/data-model.md"
)

# State and Logs
STATE_DIRS=(
  "state/projects"
)
LOG_FILES=(
  "data/processed/comparison_log.json"
  "data/processed/resource_log.jsonl"
)

# Create a temporary staging directory
STAGING_DIR=$(mktemp -d)
trap "rm -rf ${STAGING_DIR}" EXIT

echo "Staging directory: ${STAGING_DIR}"

# 1. Copy Raw Data
echo "Staging raw data..."
for dir in "${RAW_DATA_DIRS[@]}"; do
  if [ -d "${PROJECT_ROOT}/${dir}" ]; then
    cp -r "${PROJECT_ROOT}/${dir}" "${STAGING_DIR}/"
  else
    echo "Warning: Raw data directory '${dir}' not found, skipping."
  fi
done

# 2. Copy Processed Artifacts
echo "Staging processed artifacts..."
for dir in "${PROCESSED_DIRS[@]}"; do
  if [ -d "${PROJECT_ROOT}/${dir}" ]; then
    cp -r "${PROJECT_ROOT}/${dir}" "${STAGING_DIR}/"
  fi
done

# 3. Copy Results
echo "Staging results..."
for dir in "${RESULTS_DIRS[@]}"; do
  if [ -d "${PROJECT_ROOT}/${dir}" ]; then
    cp -r "${PROJECT_ROOT}/${dir}" "${STAGING_DIR}/"
  fi
done

# 4. Copy Configuration and Code Artifacts
echo "Staging configuration and code artifacts..."
mkdir -p "${STAGING_DIR}/code"
for file in "${CONFIG_FILES[@]}"; do
  if [ -f "${PROJECT_ROOT}/${file}" ]; then
    cp "${PROJECT_ROOT}/${file}" "${STAGING_DIR}/code/"
  fi
done

# 5. Copy Documentation
echo "Staging documentation..."
mkdir -p "${STAGING_DIR}/docs"
for file in "${DOCS_FILES[@]}"; do
  if [ -f "${PROJECT_ROOT}/${file}" ]; then
    cp "${PROJECT_ROOT}/${file}" "${STAGING_DIR}/docs/"
  fi
done

# 6. Copy State and Logs
echo "Staging state and logs..."
for dir in "${STATE_DIRS[@]}"; do
  if [ -d "${PROJECT_ROOT}/${dir}" ]; then
    cp -r "${PROJECT_ROOT}/${dir}" "${STAGING_DIR}/"
  fi
done

for file in "${LOG_FILES[@]}"; do
  if [ -f "${PROJECT_ROOT}/${file}" ]; then
    cp "${PROJECT_ROOT}/${file}" "${STAGING_DIR}/"
  fi
done

# 7. Generate Manifest
echo "Generating manifest..."
cd "${STAGING_DIR}"
find . -type f -print | sort > "${MANIFEST_FILE}"

# 8. Create Tarball
echo "Creating tarball..."
cd "${STAGING_DIR}"
tar -czf "${TAR_FILE}" .

# 9. Generate Checksums
echo "Generating checksums..."
sha256sum "${TAR_FILE}" > "${CHECKSUM_FILE}"

# 10. Cleanup and Finalize
echo "=== Reproducibility Package Generated Successfully ==="
echo "Package: ${TAR_FILE}"
echo "Manifest: ${MANIFEST_FILE}"
echo "Checksums: ${CHECKSUM_FILE}"
echo ""
echo "Checksum:"
cat "${CHECKSUM_FILE}"