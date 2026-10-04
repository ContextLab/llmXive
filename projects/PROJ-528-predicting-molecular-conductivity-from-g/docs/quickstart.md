# Quickstart Guide: Predicting Molecular Conductivity from Graph-Based Features

This guide walks you through the entire pipeline to compute descriptors, train models, and generate analysis reports.

## Prerequisites

- Python 3.8+
- Virtual environment (recommended)

## Setup

1. **Create and activate a virtual environment:**
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. **Install dependencies:**
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

Execute the following commands in order to run the full analysis pipeline.

### Step 1: Initialize Project Structure and Sample Data
```bash
python code/setup_structure.py
python code/run_training.py --ensure-data
```

### Step 2: Compute Molecular Descriptors
This step loads SMILES strings, validates them, and computes graph-based descriptors.
```bash
python code/run_descriptor_pipeline.py
```

### Step 3: Initialize Model Results File
Creates the `model_results.json` file with default structure if it doesn't exist.
```bash
python code/save_model_results.py --init
```

### Step 4: Run Sensitivity Analysis
Trains models with different outlier thresholds to assess stability.
```bash
python code/run_sensitivity_analysis.py
```

### Step 5: Run VIF Iterative Loop
Iteratively removes features with high VIF to reduce multicollinearity.
```bash
python code/run_huckel_vif_loop.py
```

### Step 6: Train Final Models
Trains Random Forest and Gradient Boosting models on the filtered data.
```bash
python code/train_models.py
```

### Step 7: Generate Feature Importance and Correlation Analysis
Computes permutation importance and correlation statistics.
```bash
python code/run_analysis.py
```

### Step 8: Generate Analysis Summary
Creates the final `analysis_summary.json` with top features and adjusted p-values.
```bash
python code/run_analysis_summary.py
```

### Step 9: Generate Visualizations
Creates scatter plots for top features.
```bash
python code/plot_top_features.py
```

## Validation

Verify that all expected artifacts were produced:
```bash
python code/validators.py --validate data/processed/descriptors.csv --schema contracts/descriptor_schema.yaml
python code/validators.py --validate data/processed/model_results.json --schema contracts/model_results_schema.yaml
```

Check for expected files:
- `data/processed/descriptors.csv`
- `data/processed/descriptors_base.csv`
- `data/processed/model_results.json`
- `data/processed/sensitivity_analysis.json`
- `data/processed/feature_importance.csv`
- `data/processed/analysis_summary.json`
- `data/processed/corr_plot_top5.png`
- `data/processed/corr_plot_resonance.png`

## Troubleshooting

If you encounter errors related to missing data:
1. Ensure you ran `python code/run_training.py --ensure-data` first.
2. Check that `data/raw/smiles.csv` exists and contains valid SMILES strings.
3. Verify your internet connection if the data loader attempts to fetch from external sources.