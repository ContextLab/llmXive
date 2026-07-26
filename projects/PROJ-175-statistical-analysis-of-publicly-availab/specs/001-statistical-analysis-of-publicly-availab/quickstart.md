# Quickstart: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

## Prerequisites

- Python 3.11+
- `pip`
- Access to GitHub Actions (for CI execution) or local environment with sufficient RAM.

## Installation

```bash
cd projects/PROJ-175-statistical-analysis-of-publicly-availab/code
pip install -r requirements.txt
```

## Running the Pipeline

### 1. Download Data
```bash
python data/download.py --dataset recipe1m --output data/raw/
```
*Note: FlavorDB and Counterfactual datasets are unavailable. Recipe1M is used for all data.*

### 2. Preprocess
```bash
python data/preprocess.py --input data/raw/ --output data/processed/
```
*Includes Proxy Validation and Schema Verification steps.*

### 3. Split Data
```bash
python data/split.py --input data/processed/ingredient_pairs.csv --output data/processed/
```

### 4. Fit Models
```bash
python models/logistic.py --input data/processed/train.csv --output data/logs/
python models/bayesian.py --input data/processed/train.csv --output data/logs/
```

### 5. Evaluate & Report
```bash
python evaluation/report.py --input data/logs/ --output docs/final_report.md
```

## Full Pipeline Execution

```bash
python run_full_pipeline.py
```

## Troubleshooting

- **RAM Error**: The `preprocess.py` script uses streaming. If errors persist, reduce the `--sample-size` flag.
- **Missing Dataset**: If "Counterfactual" or "FlavorDB" are missing, the script will log a warning and use Recipe1M proxies.
