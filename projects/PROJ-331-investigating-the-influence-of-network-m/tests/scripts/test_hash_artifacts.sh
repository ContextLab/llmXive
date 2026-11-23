#!/bin/bash
# test_hash_artifacts.sh
# Unit test for the hash_artifacts.sh script.
# Creates a temporary directory structure, runs the script, and verifies the output.
#
# Usage: ./tests/scripts/test_hash_artifacts.sh

set -e

# Create a temporary project structure
TEMP_ROOT=$(mktemp -d)
echo "Testing in $TEMP_ROOT"

# Setup directories
mkdir -p "$TEMP_ROOT/data/raw"
mkdir -p "$TEMP_ROOT/data/processed"
mkdir -p "$TEMP_ROOT/results"
mkdir -p "$TEMP_ROOT/figures"
mkdir -p "$TEMP_ROOT/state"

# Create dummy files
echo "dummy data content" > "$TEMP_ROOT/data/raw/test_data.nii.gz"
echo "processed data" > "$TEMP_ROOT/data/processed/adjacency.npy"
echo "result json" > "$TEMP_ROOT/results/correlation_results.json"
echo "figure png" > "$TEMP_ROOT/figures/plot.png"

# Copy the script to the temp root (adjust path logic if needed)
# We assume the script is in scripts/ relative to root
cp scripts/hash_artifacts.sh "$TEMP_ROOT/scripts/hash_artifacts.sh"
chmod +x "$TEMP_ROOT/scripts/hash_artifacts.sh"

# Run the script
cd "$TEMP_ROOT"
./scripts/hash_artifacts.sh

# Verify output file exists
if [ ! -f "state/artifacts.yaml" ]; then
    echo "FAIL: state/artifacts.yaml was not created."
    exit 1
fi

# Verify content contains expected keys
if ! grep -q "artifacts:" state/artifacts.yaml; then
    echo "FAIL: 'artifacts:' key missing."
    exit 1
fi

if ! grep -q "sha256:" state/artifacts.yaml; then
    echo "FAIL: 'sha256:' key missing."
    exit 1
fi

# Verify checksums are correct
expected_checksum=$(sha256sum data/raw/test_data.nii.gz | awk '{print $1}')
if ! grep -q "$expected_checksum" state/artifacts.yaml; then
    echo "FAIL: Checksum for test_data.nii.gz does not match."
    exit 1
fi

# Cleanup
rm -rf "$TEMP_ROOT"

echo "PASS: All tests passed."