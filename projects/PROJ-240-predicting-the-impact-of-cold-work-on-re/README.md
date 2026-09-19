# PROJ-240: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

This project implements a data pipeline to analyze how cold work and alloy composition affect recrystallization kinetics in aluminum alloys. It includes data generation, ingestion, feature engineering, model training, and statistical evaluation.

## Prerequisites

- Python 3.8+
- pip
- (Optional) Virtual environment manager (venv, conda, etc.)

## Installation

1. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Execution Guide

Follow these 5 steps to run the full analysis pipeline:

1. **Generate synthetic baseline data**:
 ```bash
 python code/generate_synthetic.py
 ```
 This creates `data/raw/synthetic_baseline.csv` and its checksum.

2. **Ingest and validate data**:
 ```bash
 python code/ingest.py
 ```
 This processes the raw data, applies physical bounds, handles missing values, clips outliers, and saves `data/processed/validated.csv` and validation reports.

3. **Engineer interaction features**:
 ```bash
 python code/engineer.py
 ```
 This calculates interaction terms (e.g., `cold_work * Mn_content`) and saves `data/processed/engineered_features.csv`.

4. **Train predictive models**:
 ```bash
 python code/train.py
 ```
 This trains Random Forest models (additive and interaction), performs cross-validation, and saves model artifacts and metrics.

5. **Evaluate statistical significance**:
 ```bash
 python code/evaluate.py
 ```
 This runs permutation tests, SHAP analysis, and generates final evaluation reports.

## Output Artifacts

- **Data**: `data/raw/`, `data/processed/`
- **Models**: `artifacts/models/`
- **Reports**: `artifacts/reports/`
- **Figures**: `figures/`

## Notes

- All scripts use deterministic seeds for reproducibility.
- The pipeline enforces strict data validation and fails loudly on errors.
- Ensure sufficient disk space for intermediate data files.

## License

Internal research use only.