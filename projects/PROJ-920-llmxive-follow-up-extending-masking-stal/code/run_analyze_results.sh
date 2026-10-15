#!/usr/bin/env bash
set -euo pipefail
python code/analyze_results.py --input data/logs/simulation_results.csv --output-dir results
