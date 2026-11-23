#!/bin/bash
# hash_artifacts.sh
# Generates SHA256 checksums for all artifacts in data/, results/, and figures/
# Updates state/artifacts.yaml with the checksums and metadata.
#
# Usage: ./scripts/hash_artifacts.sh
#
# Dependencies: sha256sum (standard on Linux/macOS), python3, pyyaml (pip install pyyaml)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"
RESULTS_DIR="$PROJECT_ROOT/results"
FIGURES_DIR="$PROJECT_ROOT/figures"
STATE_DIR="$PROJECT_ROOT/state"
STATE_FILE="$STATE_DIR/artifacts.yaml"

# Ensure state directory exists
mkdir -p "$STATE_DIR"

# Initialize a temporary file for the YAML content
TEMP_YAML=$(mktemp)
echo "artifacts:" > "$TEMP_YAML"
echo "  timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$TEMP_YAML"
echo "  checksums:" >> "$TEMP_YAML"

# Function to process a directory and append to YAML
process_directory() {
    local dir="$1"
    local label="$2"
    
    if [ ! -d "$dir" ]; then
        echo "# Directory $label does not exist, skipping." >&2
        return
    fi

    # Find all files recursively, excluding hidden files and directories
    find "$dir" -type f ! -name ".*" ! -path "*/\.*" | while read -r file; do
        # Calculate relative path from project root
        rel_path="${file#$PROJECT_ROOT/}"
        
        # Calculate SHA256
        if command -v sha256sum &> /dev/null; then
            checksum=$(sha256sum "$file" | awk '{print $1}')
        elif command -v shasum &> /dev/null; then
            # macOS fallback
            checksum=$(shasum -a 256 "$file" | awk '{print $1}')
        else
            echo "Error: Neither sha256sum nor shasum found." >&2
            exit 1
        fi

        # Get file size in bytes
        file_size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
        
        # Append to YAML (using a simple format)
        # We use a unique key based on the path (sanitized)
        safe_key=$(echo "$rel_path" | tr '/' '_')
        echo "    - path: \"$rel_path\"" >> "$TEMP_YAML"
        echo "      sha256: \"$checksum\"" >> "$TEMP_YAML"
        echo "      size_bytes: $file_size" >> "$TEMP_YAML"
        echo "      source_dir: \"$label\"" >> "$TEMP_YAML"
    done
}

# Process directories
process_directory "$DATA_DIR" "data"
process_directory "$RESULTS_DIR" "results"
process_directory "$FIGURES_DIR" "figures"

# Move the temporary file to the final location
mv "$TEMP_YAML" "$STATE_FILE"

echo "Checksums generated and saved to $STATE_FILE"

# Optional: Verify the YAML is valid using Python if pyyaml is available
if command -v python3 &> /dev/null; then
    python3 -c "import yaml; yaml.safe_load(open('$STATE_FILE'))" 2>/dev/null && echo "YAML validation successful." || echo "Warning: YAML validation failed."
fi
