# Quickstart Guide

## Prerequisites
- Python 3.11
- Virtual environment activated

## Installation
```bash
pip install -r code/requirements.txt
```

## Running the Simulation
Run the full simulation pipeline with 200 runs per beta level:
```bash
python code/run_simulation.py --runs 200 --beta-sweep 0.0,0.2,0.5,0.8,1.0
```

## Validating Results
Validate the schema of the generated summary:
```bash
python code/analysis.py validate-schema --input data/results/simulation_summary.csv
```

Run statistical tests on the results:
```bash
python code/analysis.py verify-sensitivity --input data/results/sensitivity_analysis.json
```

## Generating Visualizations
Generate bias vs beta plot:
```bash
python code/visualization.py bias_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/bias_vs_beta.png
```

Generate coverage vs beta plot:
```bash
python code/visualization.py coverage_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/coverage_vs_beta.png
```

Generate bias distribution plot:
```bash
python code/visualization.py bias_distributions --input data/results/simulation_summary.csv --output docs/paper/figures/bias_distributions.png
```