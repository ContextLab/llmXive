#!/bin/bash
# hash_artifacts.sh
# Generates SHA256 checksums for all files in data/configs, data/results, data/logs, and state.
# Satisfies Constitution Principle III (Data Hygiene) and Principle V (Versioning Discipline).
#
# Usage: ./scripts/hash_artifacts.sh [--verify]
#
# This script calls the Python utility src/utils/checksum.py.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

OUTPUT_FILE="data/configs/checksums.json"

if [ "$1" == "--verify" ]; then
    echo "Verifying artifacts against $OUTPUT_FILE..."
    python -m src.utils.checksum --verify --output "$OUTPUT_FILE"
else
    echo "Generating checksums for data/configs, data/results, data/logs, and state..."
    python -m src.utils.checksum --generate --output "$OUTPUT_FILE"
    echo "Checksums saved to $OUTPUT_FILE"
fi
