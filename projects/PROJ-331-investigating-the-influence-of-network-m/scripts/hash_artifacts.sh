#!/bin/bash
# Script to generate SHA256 checksums for artifacts and update state files

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$PROJECT_ROOT/state"
ARTIFACTS_DIR="$PROJECT_ROOT/data/processed"

mkdir -p "$STATE_DIR"

CHECKSUM_FILE="$STATE_DIR/checksums.sha256"
YAML_FILE="$STATE_DIR/artifacts.yaml"

echo "Generating checksums for artifacts in $ARTIFACTS_DIR..."

# Clear existing checksums
> "$CHECKSUM_FILE"

# Find all .npy and .json files in processed data
find "$ARTIFACTS_DIR" -type f \( -name "*.npy" -o -name "*.json" \) | while read -r file; do
    rel_path="${file#$PROJECT_ROOT/}"
    hash=$(sha256sum "$file" | awk '{print $1}')
    echo "$hash  $rel_path" >> "$CHECKSUM_FILE"
done

echo "Checksums written to $CHECKSUM_FILE"

# Generate YAML state file
echo "Updating $YAML_FILE..."
{
    echo "timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "pipeline_version: 1.0.0"
    echo "artifacts:"
    while read -r line; do
        hash=$(echo "$line" | awk '{print $1}')
        path=$(echo "$line" | awk '{print $2}')
        echo "  - path: $path"
        echo "    sha256: $hash"
    done < "$CHECKSUM_FILE"
} > "$YAML_FILE"

echo "State updated."
