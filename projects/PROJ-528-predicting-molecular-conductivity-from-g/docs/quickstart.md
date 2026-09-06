# Quickstart Guide

## Prerequisites

- Python 3.11+
- Virtual environment with dependencies installed

## Installation

1. Create virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Run Pipeline

The pipeline consists of several steps. Run them in order:

1. **Generate Descriptors**:
 ```bash
 python code/run_descriptor_pipeline.py --input data/raw/sample_smiles.csv --output data/processed/descriptors.csv
 ```

2. **Train Models and Run Sensitivity Analysis**:
 ```bash
 python code/save_model_results.py --data data/processed/descriptors.csv --output data/processed/model_results.json --sensitivity-output data/processed/sensitivity_analysis.json
 ```

3. **Run Feature Importance Analysis**:
 ```bash
 python code/feature_importance.py --data data/processed/descriptors.csv --output data/processed/feature_importance.csv
 ```

4. **Generate Analysis Summary**:
 ```bash
 python code/analysis_summary.py --feature-importance data/processed/feature_importance.csv --output data/processed/analysis_summary.json
 ```

5. **Generate Plots**:
 ```bash
 python code/plot_top_features.py --data data/processed/descriptors.csv --importance data/processed/feature_importance.csv --output data/processed/corr_plot_top5.png
 ```

## Validate Results

Check that all output files exist:
- `data/processed/descriptors.csv`
- `data/processed/model_results.json`
- `data/processed/sensitivity_analysis.json`
- `data/processed/feature_importance.csv`
- `data/processed/analysis_summary.json`
- `data/processed/corr_plot_top5.png`

## Full Pipeline Validation

Run the full validation script:
```bash
python code/run_quickstart_validation.py
```
