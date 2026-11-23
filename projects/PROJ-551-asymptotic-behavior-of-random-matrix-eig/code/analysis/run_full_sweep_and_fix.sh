#!/usr/bin/env bash
set -euo pipefail

# Run the theta sweep to generate mc_results.csv and convergence_data.json
python -m code.analysis.threshold_sweep --grid theta

# Fix the single‑run JSON artifact so that schema validation passes
python -m code.analysis.fix_single_run_json
