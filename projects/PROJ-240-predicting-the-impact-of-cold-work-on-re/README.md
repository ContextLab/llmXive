# Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

This project implements an automated science pipeline to analyze how cold work and alloy composition affect recrystallization kinetics. It generates synthetic baseline data, engineers interaction features, trains Random Forest models, and performs statistical significance testing (Permutation Test & SHAP).

## Prerequisites

- Python 3.8+
- pip

## Installation

1. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Execution Guide

Follow these 5 steps to run the full pipeline:

2. **Generate Data**:
 Creates the deterministic synthetic baseline dataset (`data/raw/synthetic_baseline.csv`).
 ```bash
 python code/generate_synthetic.py
 ```

3. **Ingest & Engineer**:
 Validates, cleans, clips outliers, and engineers interaction features. Outputs `data/processed/final_dataset.csv`.
 ```bash
 python code/ingest.py
 python code/engineer.py
 python code/finalize_dataset.py
 ```

4. **Train**:
 Trains the Random Forest model, performs cross-validation, and evaluates on the test set. Outputs `artifacts/models/kinetic_model.pkl` and metrics.
 ```bash
 python code/train.py
 ```

5. **Evaluate**:
 Runs the Additive vs. Interaction model comparison (Permutation Test) and SHAP analysis. Outputs `artifacts/reports/statistical_significance.json` and `artifacts/reports/shap_interaction_report.json`.
 ```bash
 python code/evaluate.py
 ```

## Output Artifacts

- **Data**: `data/processed/final_dataset.csv`
- **Models**: `artifacts/models/kinetic_model.pkl`, `artifacts/models/additive_model.pkl`
- **Reports**:
 - `artifacts/reports/training_metrics.json`
 - `artifacts/reports/statistical_significance.json`
 - `artifacts/reports/shap_interaction_report.json`

## Notes

- The pipeline uses a fixed random seed (42) for reproducibility.
- Synthetic data is the primary source as per project specification.
- Ensure `code/config.py` settings (e.g., `N_ROWS_TARGET`, `N_ESTIMATORS`) are adjusted if needed before running.
