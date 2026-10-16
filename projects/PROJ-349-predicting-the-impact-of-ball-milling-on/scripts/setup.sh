#!/usr/bin/env bash
# setup.sh - Creates the project directory structure based on the manifest
# Reads scripts/setup_manifest.txt and creates directories/files listed there.

set -e

# Determine the location of this script and the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

MANIFEST_PATH="${PROJECT_ROOT}/scripts/setup_manifest.txt"

if [[ ! -f "$MANIFEST_PATH" ]]; then
    echo "Manifest file not found at $MANIFEST_PATH"
    exit 1
fi

echo "Reading manifest from $MANIFEST_PATH"

while IFS= read -r line; do
    # Trim leading/trailing whitespace
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"

    # Skip empty lines and comments
    [[ -z "$line" || "$line" == \#* ]] && continue

    # If the line ends with a slash, treat it as a directory
    if [[ "$line" == */ ]]; then
        dir_path="${line%/}"
        full_path="${PROJECT_ROOT}/${dir_path}"
        if [[ ! -d "$full_path" ]]; then
            mkdir -p "$full_path"
            echo "Created directory: $full_path"
        else
            echo "Directory already exists: $full_path"
        fi
    else
        # Otherwise treat it as a file: ensure its parent directory exists, then touch the file
        file_path="${PROJECT_ROOT}/${line}"
        parent_dir="$(dirname "$file_path")"
        mkdir -p "$parent_dir"
        if [[ ! -f "$file_path" ]]; then
            touch "$file_path"
            echo "Created file: $file_path"
        else
            echo "File already exists: $file_path"
        fi
    fi
done < "$MANIFEST_PATH"

echo "Setup complete."
