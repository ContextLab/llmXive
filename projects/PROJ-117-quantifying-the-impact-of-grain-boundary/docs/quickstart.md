# Quickstart Guide

This guide provides a step-by-step walkthrough to run the grain boundary diffusivity pipeline.

## Overview

The pipeline performs the following steps:
1. **Download** raw data from external sources (Materials Project, OpenKIM)
2. **Parse** geometry features from crystal structures
3. **Preprocess** and validate the dataset
4. **Train** an XGBoost model to predict diffusivity
5. **Validate** the model with cross-validation and bias testing
6. **Interpret** results with SHAP analysis

## Prerequisites

- Follow the [Installation Guide](installation.md) to set up your environment
- Ensure you have valid API keys for Materials Project (and OpenKIM if applicable)
- Have at least 7 GB of available RAM [UNRESOLVED-CLAIM: c_00d75107 — status=not_enough_info]

## Step-by-Step Execution

### 1. Setup Environment

```bash
python code/setup_env.py
```

This validates your API keys and loads environment variables.

### 2. Download Data

```bash
python code/download.py
```

This script:
- Fetches grain boundary data from Materials Project and OpenKIM
- Validates JSON schema
- Saves raw files to `data/raw/` with checksums
- Ensures at least 500 records are retrieved

**Output:** `data/raw/` directory with raw structure files

### 3. Parse Geometry

```bash
python code/geometry_parser.py
```

This script:
- Parses POSAR/CIF files using pymatgen
- Extracts boundary plane normals, Σ values, and other features
- Encodes misorientation as Rodrigues vectors
- Saves intermediate data to `data/processed/parsed_geometry.parquet`

**Output:** `data/processed/parsed_geometry.parquet`

### 4. Preprocess Data

```bash
python code/preprocess.py
```

This script:
- Loads parsed geometry data
- Filters records with missing required features
- Tags metadata features (simulation_method, potential_id)
- Enforces minimum record count (n >= 500)
- Saves cleaned dataset to `data/processed/cleaned_dataset.parquet`

**Output:** `data/processed/cleaned_dataset.parquet`

### 5. Run Diagnostics (Optional but Recommended)

```bash
python code/diagnostics.py
```

This script:
- Computes Mutual Information between misorientation angle and Σ value
- Logs warnings for high MI values
- Saves collinearity diagnostic to `artifacts/reports/collinearity_diagnostic.json`

**Output:** `artifacts/reports/collinearity_diagnostic.json`

### 6. Train Model

```bash
python code/train.py
```

This script:
- Performs 70/15/15 train/validation/test split
- Runs RandomizedSearchCV for XGBoost hyperparameter tuning
- Trains final model on training set
- Evaluates on test set and logs metrics
- Saves model to `models/best_model.json`

**Output:**
- `models/best_model.json`
- `artifacts/reports/training_metrics.json`

### 7. Validate Model

```bash
python code/validate.py
```

This script:
- Performs 5 (2604.10702, https://arxiv.org/abs/2604.10702)-fold cross-validation
- Calculates R², RMSE, MAPE with standard deviation
- Runs regression bias test with Bonferroni correction
- Generates validation report

**Output:** `artifacts/reports/validation_report.json`

### 8. Interpret Results

```bash
python code/interpret.py
```

This script:
- Generates SHAP summary plot
- Performs sensitivity analysis on R² threshold
- Saves plots to `artifacts/figures/`
- Generates threshold variation table

**Output:**
- `artifacts/figures/shap_summary.png`
- `artifacts/reports/threshold-variation-table.csv`

## Full Pipeline Execution

To run the entire pipeline sequentially:

```bash
bash scripts/run_pipeline.sh # If available, or run each step manually
```

Or manually:

```bash
python code/setup_env.py && \
python code/download.py && \
python code/geometry_parser.py && \
python code/preprocess.py && \
python code/diagnostics.py && \
python code/train.py && \
python code/validate.py && \
python code/interpret.py
```

## Expected Outputs

After successful execution, you should have:

```
data/
├── raw/
│ └── [raw structure files]
└── processed/
 ├── parsed_geometry.parquet
 └── cleaned_dataset.parquet

models/
└── best_model.json

artifacts/
├── reports/
│ ├── collinearity_diagnostic.json
│ ├── training_metrics.json
│ ├── validation_report.json
│ └── threshold-variation-table.csv
└── figures/
 └── shap_summary.png
```

## Validation

To verify the pipeline completed successfully:

```bash
python code/validate_quickstart.py
```

This script checks:
- All required directories exist
- All expected output files are present
- Dependencies are correctly installed
- Pipeline scripts are executable

## Troubleshooting

### "Data Insufficiency" Error

If you see "Data Insufficiency: Retrieved {count} < 500", ensure:
- Your API keys are valid and have sufficient quota
- The search keywords match available data
- You have network connectivity to the APIs

### Memory Errors

If the pipeline exceeds 7 GB RAM:
- Close other applications
- Ensure you're using 64-bit Python
- Consider running on a machine with more RAM

### API Rate Limiting

If you encounter rate limiting:
- Wait and retry
- Check your API plan limits
- Consider caching downloaded data

## Next Steps

- Review the [API Reference](api_reference.md) for detailed module documentation
- Explore the [Data Schema](data_schema.md) to understand the data structure
- Read the [README.md](../README.md) for project overview
- Run unit tests: `pytest tests/`
- Run integration tests: `pytest tests/integration/`
