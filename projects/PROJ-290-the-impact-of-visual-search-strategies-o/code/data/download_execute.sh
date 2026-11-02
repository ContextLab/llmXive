#!/usr/bin/env bash
set -e
# Execute the download script with its default fallback dataset.
python "$(git rev-parse --show-toplevel)/code/data/download.py"
# Verify that the expected files exist.
RAW_DIR="$(python -c 'from config import get_config; print(get_config().get_path(\"data_raw\"))')"
if [ ! -d "$RAW_DIR" ]; then
  echo "Raw data directory not found: $RAW_DIR" >&2
  exit 1
fi
ZIP_FILE=$(ls "$RAW_DIR"/*.zip | head -n1)
if [ -z "$ZIP_FILE" ]; then
  echo "No ZIP archive found in $RAW_DIR" >&2
  exit 1
fi
if [ ! -f "$RAW_DIR/checksum.txt" ]; then
  echo "Checksum file not found in $RAW_DIR" >&2
  exit 1
fi
echo "Download script completed successfully. Archive: $ZIP_FILE"
echo "Checksum file: $RAW_DIR/checksum.txt"