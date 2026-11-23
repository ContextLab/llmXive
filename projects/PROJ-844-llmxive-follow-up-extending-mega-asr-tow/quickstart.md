# Quickstart Guide

## Prerequisites
- Python 3.10+
- pip

## Setup
```bash
pip install -r requirements.txt
```

## Run the Pipeline

### 1. Download and Verify Datasets
```bash
python code/data_loader.py --download
```

### 2. Verify Dataset Coverage
```bash
python code/data_loader.py --coverage
```

### 3. Generate Human Validation Template
```bash
python code/human_validation.py --generate
```

### 4. Run Sensitivity Analysis and Generate Reports
```bash
python code/analysis.py --validate-sss
```

## Output Artifacts
- `data/derived/sensitivity_analysis.csv`
- `data/derived/regression_results.json`
- `data/validation/human_annotations.csv`