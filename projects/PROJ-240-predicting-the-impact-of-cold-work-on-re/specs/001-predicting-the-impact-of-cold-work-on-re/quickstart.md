# Quickstart: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

## Prerequisites

- Python 3.11+
- `pip` or `poetry`
- Access to a standard GitHub Actions runner (2 CPU, 4GB RAM) or local environment.

## Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   git clone <repo-url>
   cd projects/PROJ-240-predicting-the-impact-of-cold-work-on-re
   ```

2. **Install dependencies**.
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` is located in `code/` and includes pandas, scikit-learn, shap, numpy, pytest.*

## Running the Pipeline

The pipeline is designed to run end-to-end via the main entry point.

### Step 1: Generate & Ingest Data
```bash
python code/main.py --step generate
```
- Generates synthetic data (seed=42, 1,000 rows).
- Performs cleaning and outlier clipping.
- Saves `data/raw_synthetic.csv` and `data/cleaned_data.csv`.

### Step 2: Feature Engineering
```bash
python code/main.py --step engineer
```
- Creates interaction features (`cold_work * Mn`, etc.).
- Saves `data/engineered_features.csv`.

### Step 3: Train & Evaluate
```bash
python code/main.py --step train
```
- Splits data (80/20, seed=42).
- Trains Random Forest with k-fold cross-validation.
- Runs **Delta-Permutation Test** and **SHAP Interaction Analysis**.
- Outputs `data/metrics.json` and `data/shap_summary.json`.

### Step 4: Validation (Tests)
```bash
pytest tests/
```
- Verifies data generation, feature engineering, and model performance thresholds.

## Expected Outputs

- **`data/engineered_features.csv`**: The final dataset used for modeling.
- **`data/metrics.json`**: Contains R², MAE, CV scores, and permutation p-value.
- **`data/shap_summary.json`**: Feature importance rankings (including interaction values).
- **`results/figures/`**: (Optional) Plots of feature importance and residual distributions.

## Troubleshooting

- **Error: Dataset size < 50**: The generator may have failed. Check `data/raw_synthetic.csv`.
- **Error: Insufficient Power**: If the dataset is < 500 rows, the permutation test may be underpowered. Ensure the generator is producing a sufficient volume of rows as per the research plan.
- **Memory Error**: Ensure dataset size is <10,000 rows (configured in `config.py`).
- **No Verified Dataset**: This project relies on synthetic data. Do not attempt to fetch external datasets unless a verified source is added to the spec.