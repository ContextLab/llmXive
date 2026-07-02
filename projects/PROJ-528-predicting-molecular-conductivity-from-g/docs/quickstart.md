# Quickstart Guide: Predicting Molecular Conductivity

This guide walks you through running the full pipeline to predict molecular conductivity from graph-based features.

## Prerequisites
- Python 3.11 or higher
- pip (Python package installer)

## 1. Setup Environment
```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Prepare Data
The pipeline expects a CSV file containing SMILES strings and conductivity values (or HOMO-LUMO gap as a fallback).
Place your data file in `data/raw/` (e.g., `data/raw/molecules.csv`).

Ensure the CSV has columns: `smiles` and `conductivity` (or `HOMO_LUMO_gap`).

## 3. Run the Pipeline

### Step 3.1: Compute Descriptors
This step parses SMILES, validates structures, and computes graph-based and physics-informed descriptors (including resonance energy and bond polarity).
```bash
python code/run_descriptor_pipeline.py --input data/raw/molecules.csv --output data/processed/descriptors.csv
```
*Output*: `data/processed/descriptors.csv` containing computed features.

### Step 3.2: Train Models
This step splits data (scaffold split), trains Random Forest and Gradient Boosting models, and performs sensitivity analysis.
```bash
python code/run_training.py --input data/processed/descriptors.csv
```
*Output*: `data/processed/model_results.json` and `data/processed/sensitivity_analysis.json`.

### Step 3.3: Feature Analysis
This step calculates VIF, applies iterative retraining, and generates feature importance plots.
```bash
python code/run_feature_analysis.py --input data/processed/descriptors.csv
```
*Output*: `data/processed/feature_importance.csv`, `data/processed/corr_plot_top5.png`, and `data/processed/analysis_summary.json`.

## 4. Review Results
- **Model Performance**: Check `data/processed/model_results.json` for R² and MAE scores.
- **Feature Importance**: View `data/processed/feature_importance.csv` to see which descriptors (e.g., resonance_energy, bond_polarity) drive predictions.
- **Visualizations**: Open `data/processed/corr_plot_top5.png` for scatter plots of top features.

## 5. Validation
To verify the pipeline against the reviewer's feedback on resonance:
- Inspect the `resonance_energy` column in `data/processed/descriptors.csv`.
- Check `docs/REVIEWER_FEEDBACK_RESOLUTION.md` for details on how resonance and bond length contraction were modeled.

## Troubleshooting
- **Invalid SMILES**: Ensure all SMILES strings in your input file are valid. The pipeline will log invalid entries.
- **Missing Target**: If `conductivity` is missing, the pipeline will attempt to use `HOMO_LUMO_gap` (with a warning).
- **VIF Issues**: If VIF > 10, the pipeline automatically iteratively removes high-VIF features. Check `data/processed/analysis_summary.json` for the final feature set.
