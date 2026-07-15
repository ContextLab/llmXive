#!/bin/bash
# hash_artifacts.sh
# Generates SHA256 checksums for project artifacts and updates state/manifest.yaml
#
# Usage: ./scripts/hash_artifacts.sh
#
# This script:
# 1. Scans specific directories for files to hash
# 2. Computes SHA256 checksums
# 3. Updates state/manifest.yaml with the results
# 4. Prints a summary to stdout

set -e

# Project root (assuming script is run from root or we resolve it)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Directories to scan for artifacts
SCAN_DIRS=(
    "code"
    "data/processed"
    "data/raw"
    "results"
    "state"
)

# Output file
STATE_FILE="$PROJECT_ROOT/state/manifest.yaml"
CHECKSUM_FILE="$PROJECT_ROOT/state/checksums.txt"

# Ensure state directory exists
mkdir -p "$PROJECT_ROOT/state"

echo "Starting artifact hashing at $(date)"
echo "Project root: $PROJECT_ROOT"
echo "Output manifest: $STATE_FILE"

# Initialize the checksum file
> "$CHECKSUM_FILE"

# Arrays to hold data for YAML
declare -A file_hashes

# Scan directories
for dir in "${SCAN_DIRS[@]}"; do
    full_path="$PROJECT_ROOT/$dir"
    if [ -d "$full_path" ]; then
        echo "Scanning: $dir"
        while IFS= read -r -d '' file; do
            # Skip the checksum file itself to avoid recursion issues if re-running
            if [[ "$file" == *"$CHECKSUM_FILE" ]]; then
                continue
            fi

            # Compute relative path from project root
            rel_path="${file#$PROJECT_ROOT/}"
            
            # Compute SHA256
            hash=$(sha256sum "$file" | cut -d' ' -f1)
            
            # Store for YAML generation
            file_hashes["$rel_path"]="$hash"
            
            # Write to checksum file
            echo "$hash  $rel_path" >> "$CHECKSUM_FILE"
        done < <(find "$full_path" -type f -print0 2>/dev/null)
    else
        echo "Warning: Directory $dir does not exist, skipping."
    fi
done

# Generate YAML manifest
{
    echo "# Artifact Manifest"
    echo "# Generated automatically by scripts/hash_artifacts.sh"
    echo "# Timestamp: $(date -Iseconds)"
    echo ""
    echo "version: 1.0"
    echo "generated_at: $(date -Iseconds)"
    echo "files:"
    
    for key in "${!file_hashes[@]}"; do
        # YAML indentation: 2 spaces for list items, 4 for key
        echo "  - path: $key"
        echo "    sha256: ${file_hashes[$key]}"
    done
} > "$STATE_FILE"

echo ""
echo "Hashing complete."
echo "Checksums written to: $CHECKSUM_FILE"
echo "Manifest updated at: $STATE_FILE"
echo "Total files hashed: ${#file_hashes[@]}"
echo "Finished at $(date)"
