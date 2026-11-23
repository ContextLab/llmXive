#!/usr/bin/env bash
set -e

# 1) Verify environment and write checksums
python -m code.src.env_check

# 2) Run the full end‑to‑end analysis (ingestion + proxy agreement + summary)
python -m code.src.run_e2e
