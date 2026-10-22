#!/usr/bin/env bash
set -euo pipefail

# Activate the virtual environment if it exists (quickstart helper)
source "$(dirname "${BASH_SOURCE[0]}")/quickstart.sh"

# Run the minimal pipeline (50 clips)
python -m src.pipeline.run_all --subset 50
