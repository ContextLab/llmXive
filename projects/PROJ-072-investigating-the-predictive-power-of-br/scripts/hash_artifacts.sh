#!/bin/bash
# scripts/hash_artifacts.sh
# Generates SHA-256 hashes for all files in `data/` and `code/`
# and updates the `state/artifacts.yaml` file with the checksums.
#
# This script enforces Constitution Principle V (Data Integrity & Provenance).

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/data"
CODE_DIR="${PROJECT_ROOT}/code"
STATE_DIR="${PROJECT_ROOT}/state"
STATE_FILE="${STATE_DIR}/artifacts.yaml"

# Ensure state directory exists
mkdir -p "${STATE_DIR}"

echo "Generating SHA-256 hashes for artifacts..."
echo "Data directory: ${DATA_DIR}"
echo "Code directory: ${CODE_DIR}"

# Initialize a temporary file for the YAML content
TEMP_YAML=$(mktemp)

# Write YAML header
cat > "${TEMP_YAML}" << EOF
# Auto-generated artifact hashes
# Generated at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# Constitution Principle V: Integrity Verification
hashes:
  data:
EOF

# Hash files in data/
if [ -d "${DATA_DIR}" ]; then
    find "${DATA_DIR}" -type f \( -name "*.csv" -o -name "*.npy" -o -name "*.json" -o -name "*.yaml" -o -name "*.txt" -o -name "*.png" \) | sort | while read -r file; do
        rel_path="${file#${DATA_DIR}/}"
        hash=$(sha256sum "${file}" | cut -d' ' -f1)
        echo "    - path: ${rel_path}" >> "${TEMP_YAML}"
        echo "      sha256: ${hash}" >> "${TEMP_YAML}"
    done
else
    echo "    - path: (none)" >> "${TEMP_YAML}"
    echo "      sha256: (directory not found)" >> "${TEMP_YAML}"
fi

echo "  code:" >> "${TEMP_YAML}"

# Hash files in code/
if [ -d "${CODE_DIR}" ]; then
    find "${CODE_DIR}" -type f -name "*.py" | sort | while read -r file; do
        rel_path="${file#${CODE_DIR}/}"
        hash=$(sha256sum "${file}" | cut -d' ' -f1)
        echo "    - path: ${rel_path}" >> "${TEMP_YAML}"
        echo "      sha256: ${hash}" >> "${TEMP_YAML}"
    done
else
    echo "    - path: (none)" >> "${TEMP_YAML}"
    echo "      sha256: (directory not found)" >> "${TEMP_YAML}"
fi

# Move the temporary file to the final location
mv "${TEMP_YAML}" "${STATE_FILE}"

echo "Successfully updated ${STATE_FILE}"
echo "Total artifacts hashed:"
grep -c "sha256:" "${STATE_FILE}" || echo "0"