# Quickstart Guide

## Prerequisites
- Python 3.8+
- pip dependencies (see requirements.txt)

## Installation
```bash
pip install -r requirements.txt
```

## Verify Configuration
```bash
python code/verify_config.py
```

## Run Full Analysis Pipeline
This command generates data, runs scaling analysis, and applies statistical corrections.
```bash
python code/main.py --mode generate_and_analyze --Llist 100 200 400 800 1600 --Wlist 0.5 0.75 1.0 1.25 1.5 1.75 2.0 2.5 3.0 5.0 --realizations 100 --seed 42
```

## Run Scaling Analysis Only
```bash
python code/main.py --mode scaling_analysis --Llist 100 200 400 800 1600 --Wlist 0.5 0.75 1.0 1.25 1.5 1.75 2.0 2.5 3.0 5.0 --realizations 100 --seed 42 --output data/processed/scaling_results.csv
```

## Run Visualization
```bash
python code/main.py --mode visualize --L 200 --W 2.0 --realization 5 --output figures/eigenstate_decay.png
```

## Output Artifacts
- `data/processed/scaling_fits.json`: Finite‑size scaling results
- `data/processed/bonferroni_results.json`: Bonferroni‑corrected statistical results
- `data/metadata/residuals.json`: Numerical stability logs
- `figures/`: Generated plots