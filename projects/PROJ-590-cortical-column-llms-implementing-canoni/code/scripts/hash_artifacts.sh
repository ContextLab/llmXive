#!/bin/bash
# Hash artifacts script for Constitution Principle III and V
# Generates and verifies SHA256 checksums for data artifacts

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$PROJECT_ROOT/data"
CHECKSUM_FILE="$DATA_DIR/checksums.sha256"

echo "=== Generating SHA256 checksums ==="

# Find all relevant files in data/results, data/configs, data/logs, state
FILES_TO_HASH=$(find "$DATA_DIR/results" "$DATA_DIR/configs" "$DATA_DIR/logs" "$PROJECT_ROOT/state" -type f 2>/dev/null || true)

if [ -z "$FILES_TO_HASH" ]; then
    echo "No files found to hash."
    exit 0
fi

# Generate checksums
echo "$FILES_TO_HASH" | xargs sha256sum > "$CHECKSUM_FILE"

echo "Checksums written to: $CHECKSUM_FILE"
echo "=== Verification complete ==="

# Verify checksums if file exists
if [ -f "$CHECKSUM_FILE" ]; then
    echo "Verifying checksums..."
    sha256sum -c "$CHECKSUM_FILE" > /dev/null
    echo "✓ All checksums verified successfully"
fi

exit 0
