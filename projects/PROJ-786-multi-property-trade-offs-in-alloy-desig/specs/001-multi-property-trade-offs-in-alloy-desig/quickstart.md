# Quickstart: Multi-Property Trade-Offs in Alloy Design

## Prerequisites
- Python 3.11+
- Git
- Access to HuggingFace (public, no token needed for this dataset)

## Installation

1. **Clone and Setup**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-786-multi-property-trade-offs-in-alloy-desig
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Full Pipeline
Execute the entire workflow (Ingestion -> Encoding -> Training -> Optimization -> Analysis):
```bash
python code/main.py
```
This will:
1. Download OQMD data to `data/raw/`.
2. Generate `data/processed/encoded_alloys.csv`.
3. Train models and generate `data/processed/model_validation_report.json` and `data/processed/loso_test_points.csv`.
4. Run NSGA-II and save `data/processed/pareto_frontier.csv`.
5. Perform LCE and sensitivity analysis, saving `data/processed/sensitivity_analysis.csv`.
6. Run versioning hook to update `state/` YAML.

### Individual Steps
- **Ingestion & Encoding**:
  ```bash
  python code/ingestion.py --output data/processed/encoded_alloys.csv
  ```
- **Model Training**:
  ```bash
  python code/training.py --input data/processed/encoded_alloys.csv --output data/processed/model_validation_report.json
  ```
- **Optimization**:
  ```bash
  python code/optimization.py --input data/processed/encoded_alloys.csv --output data/processed/pareto_frontier.csv
  ```
- **Analysis**:
  ```bash
  python code/analysis.py --input data/processed/encoded_alloys.csv --output data/processed/sensitivity_analysis.csv
  ```

## Verifying Results

1. **Check Data Integrity**:
   ```bash
   python -c "import pandas as pd; df = pd.read_csv('data/processed/encoded_alloys.csv'); print(df.isnull().sum())"
   ```
   Ensure all counts are 0.

2. **Check Model Performance**:
   ```bash
   python -c "import json; d = json.load(open('data/processed/model_validation_report.json')); print(f\"Mean R2: {d['mean_r2']}\")"
   ```
   Ensure `mean_r2` > 0.6.

3. **Check Sensitivity Output**:
   ```bash
   python -c "import pandas as pd; df = pd.read_csv('data/processed/sensitivity_analysis.csv'); print(df.head())"
   ```
   Ensure `threshold` ranges from 0.1 to 0.9.

## Troubleshooting

- **Error: "Insufficient data"**: The OQMD subset loaded has < 500 valid entries. Check network connectivity or try the backup URL in `code/ingestion.py`.
- **Error: "Convex Hull"**: If the convex hull calculation fails, ensure at least 3 non-collinear points exist in the training set.
- **Timeout**: If the pipeline exceeds 6 hours, reduce `NSGA_POPULATION_SIZE` and `NSGA_GENERATIONS` in `code/config.py`.