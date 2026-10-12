#!/usr/bin/env bash
set -e
echo "Running reproducibility script..."
pip install -r code/requirements.txt
python -m simulation.runner --grid-config specs/001-investigating-the-stability-of-rotating/grid_config.json --repeats 5 --output-dir data/raw
python -m statistics.aggregators data/processed/metrics.csv data/aggregated/statistical_results.json
python -m viz.plotter --input data/aggregated/statistical_results.json --output-dir figures
echo "Success"
