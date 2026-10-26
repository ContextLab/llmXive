#!/usr/bin/env bash
set -euo pipefail

# Ensure a GitHub token is present; the script will abort otherwise.
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "Error: GITHUB_TOKEN environment variable is not set."
  exit 1
fi

# Run the data extraction script in full mode (>=500 rows).
python -m code.data_extraction --full
