#!/usr/bin/env bash
set -e
# Ensure the environment is set up (dependencies installed)
python -m pip install -r code/requirements.txt
# Run the full primary simulation sweep
python code/main.py --mode full --seed 42
echo "Primary simulation sweep completed."
ls -lh data/results/estimation_results.csv data/results/simulation_raw.json