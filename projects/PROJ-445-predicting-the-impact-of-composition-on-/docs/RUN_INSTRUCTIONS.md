# Run Instructions

This guide details the step-by-step execution of the Chalcogenide Glass Transition Prediction pipeline.

## Prerequisites
- Python 3.11 or higher
- `pip` package manager
- Network access (to download the dataset)

## Step 1: Environment Setup

1. Create a virtual environment (recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Step 2: Initialize Directories

Run the setup script to ensure all required directories (`data/`, `artifacts/`, `state/`, etc.) exist:
```bash
python code/setup_directories.py
```

## Step 3: Execute the Pipeline

The pipeline is executed in sequential stages. Run each command in order.

### 3.1 Download Data
Fetches the raw dataset and validates required columns.
```bash
python code/src/data/download.py
```
*Expected Output*: Confirmation of download, validation logs, and hash registration in `state/manifest.json`.

### 3.2 Preprocess Data
Computes features (MCN, electronegativity variance, etc.) and performs power analysis.
```bash
python code/src/data/preprocess.py
```
*Expected Output*: `data/processed/processed_data.csv` and `state/power_analysis.json`.

### 3.3 Split Data
Performs stratified split or LOFO CV based on family sizes.
```bash
python code/src/data/split.py
```
*Expected Output*: `data/splits/train_indices.json` and `data/splits/test_indices.json`.

### 3.4 Train Models
Trains Linear and Gradient Boosting models. Handles collinearity mitigation if VIF >= 5.
```bash
python code/src/models/train.py
```
*Expected Output*: Model pickles in `data/models/` and `data/residualized/` (if applicable).

### 3.5 Evaluate Models
Computes RMSE and R² on the test set.
```bash
python code/src/models/evaluate.py
```
*Expected Output*: `artifacts/performance_metrics.json` (partial).

### 3.6 Explain Models (SHAP)
Computes SHAP values and transferability metrics.
```bash
python code/src/models/explain.py
```
*Expected Output*: SHAP results and LOFO model artifacts.

### 3.7 Generate Final Reports
Aggregates metrics and generates the final Markdown report.
```bash
python code/src/utils/generate_metrics.py
```
*Expected Output*: `artifacts/shap_report.md` and complete `artifacts/performance_metrics.json`.

### 3.8 Finalize Manifest
Records final hashes for all artifacts.
```bash
python code/src/utils/manifest_finalizer.py
```

## Step 4: Verification

1. Check `state/manifest.json` to ensure all artifacts are recorded.
2. Review `artifacts/shap_report.md` for scientific findings.
3. Run the test suite to verify integrity:
 ```bash
 pytest code/tests/ -v
 ```

## Troubleshooting

- **Missing Columns**: If the download fails due to missing columns, check the network connection and the source URL in `src/data/download.py`. The error will be logged to `state/variable_fit.log`.
- **Small Families**: If a chemical family has <10 samples, the pipeline automatically switches to LOFO. Check `data/splits/lofo_families.json` to see which families were used.
- **Collinearity**: If VIF >= 5, residualized features are generated. Check `data/residualized/` for these files.
- **Power Limitation**: If power < 0.80, a warning is included in the final report. Check `state/power_analysis.json`.

## Performance Constraints
- **Time Limit**: The full pipeline (5-fold CV) is designed to complete within 6 hours on a standard CPU runner.
- **Memory**: Uses ~7GB RAM max. No GPU required.
- **Data**: Uses real data only; no synthetic generation.
