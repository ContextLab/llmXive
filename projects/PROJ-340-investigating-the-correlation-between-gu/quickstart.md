# Quickstart Guide

## Prerequisites
- Python 3.11+
- pip

## Setup
```bash
pip install pandas numpy scipy scikit-learn pyyaml
```

## Execution
1. Generate Synthetic Data & Manifest (T006c, T006):
 ```bash
 python code/data_generator.py --output data/raw/synthetic_data.csv --output-manifest data/metadata/synthetic_data_manifest.json
 ```

2. Generate Large Proxy (T070):
 ```bash
 python code/generate_large_proxy.py --output data/raw/large_proxy.csv
 ```

3. Run Main Pipeline (Ingest -> Analyze -> Report):
 ```bash
 python code/main.py --input data/raw/synthetic_data.csv --output data/results/
 ```

## Verification
Check `data/results/final_report.json` for the output.