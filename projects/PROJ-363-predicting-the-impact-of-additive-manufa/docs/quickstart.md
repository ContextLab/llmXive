# Quick Start Guide

This guide provides the exact commands to run the full pipeline from scratch on a fresh environment.

## 1. Environment Setup

Ensure you have Python 3.9 or higher installed. Create a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## 2. Run the Pipeline

Execute the following scripts in order. Each script writes its output to the `data/`, `models/`, or `results/` directories and updates `state.yaml`.

### A. Download Data

{{claim:c_1a784bee}} (2102.02470, https://arxiv.org/abs/2102.02470) This step verifies the material type to ensure data integrity.

```bash
python code/download_data.py
```

**Expected Output**:
- `data/raw/<dataset_name>.csv`
- Log message confirming "Material Mismatch" check passed.

### B. Preprocess Data

Cleans the data, imputes missing values, normalizes features, and engineers the Volumetric Energy Density feature.

```bash
python code/preprocess.py
```

**Expected Output**:
- `data/processed/cleaned_316L.csv`
- `data/processed/X_raw.csv`
- `data/processed/X_derived.csv`
- Log message confirming schema validation and degenerate dataset check.

### C. Train Models

Trains Gradient Boosting and MLP models on both raw and derived feature sets using 5-fold cross-validation. [UNRESOLVED-CLAIM: c_eaf7d827 — status=not_enough_info]

```bash
python code/train_models.py
```

**Expected Output**:
- `models/artifacts/` containing `.pkl` files.
- `results/reports/model_metrics_raw.json`
- `results/reports/model_metrics_derived.json`

### D. Analyze Explainability

Generates SHAP plots and statistical significance reports (Permutation Importance + Bootstrap CIs).

```bash
python code/analyze_explainability.py
```

**Expected Output**:
- `results/plots/shap_summary_raw.png`
- `results/plots/shap_summary_derived.png`
- `results/reports/significance_report_raw.json`
- `results/reports/significance_report_derived.json`

## 3. Verify Artifacts

Confirm that all generated files match the expected checksums recorded in `state.yaml`.

```bash
python code/verify_artifacts.py
```

If the script exits with code 0, the pipeline has successfully completed and all artifacts are valid.

## Troubleshooting

- **Network Errors**: If `download_data.py` fails, ensure your network connection is active. The script does not use synthetic fallbacks; it will raise an exception if the real data source is unreachable.
- **Schema Validation Errors**: If `preprocess.py` fails, check that the downloaded raw data matches the expected columns defined in `contracts/dataset.schema.yaml`.
- **Memory Issues**: If training fails due to memory, ensure your environment has at least 8GB of RAM available [UNRESOLVED-CLAIM: c_d533c9f1 — status=not_enough_info]. The pipeline uses 5-fold CV which loads data multiple times. [UNRESOLVED-CLAIM: c_c57057cc — status=not_enough_info]
