#!/usr/bin/env bash
set -e

# Run the Python environment‑check module.  It will exit with status 0
# only when all required imports succeed and the checksum file has been
# written.
python -m src.env_check
