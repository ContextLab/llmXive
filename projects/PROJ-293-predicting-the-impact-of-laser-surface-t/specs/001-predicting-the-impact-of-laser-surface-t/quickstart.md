# Quickstart: Predicting the Impact of Laser Surface Texturing on Wear Resistance

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local environment with sufficient RAM)

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-293-predicting-the-impact-of-laser-surface-t
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins `scikit-learn`, `pandas`, `shap`, `numpy`, and `statsmodels`.*

4.  **Verify Directory Structure**:
    Ensure the following directories exist. If not, create them:
    ```bash
    mkdir -p code data/raw data/processed data/intermediate models reports tests state
    ```

## Running the Pipeline

Execute the full pipeline end-to-end:

```bash
python -m code.main ingest && \
python -m code.main preprocess && \
python -m code.main train && \
python -m code.main interpret && \
python -m code.main report
```

### Step-by-Step Breakdown

1.  **Ingestion (`ingest`)**:
    - Downloads data from the verified sources listed in `specs/001-predicting-the-impact-of-laser-surface-t/research.md`.
    - Maps columns to the canonical schema.
    - Calculates SHA‑256 checksums and updates `state/projects/PROJ-293-predicting-the-impact-of-laser-surface-t.yaml`.
    - Outputs `data/intermediate/merged.csv`.

2.  **Preprocessing (`preprocess`)**:
    - Drops records with missing required predictors.
    - Applies Archard's law normalization (or flags as `raw`).
    - Runs Shapiro‑Wilk/Levene's tests on the raw subset.
    - Performs VIF reduction (deterministic strategy).
    - Outputs `data/processed/cleaned.csv`.

3.  **Training (`train`)**:
    - Runs GridSearchCV (≥10 combos) using a scikit‑learn `Pipeline` to prevent leakage.
    - Performs Leave‑One‑Material‑Class‑Out CV (or K‑Fold fallback).
    - Saves the best model to `models/best_model.pkl`.

4.  **Interpretation (`interpret`)**:
    - Computes SHAP values.
    - Runs permutation significance testing.
    - Applies the causal‑language filter to the final report.
    - Generates plots in `reports/`.

## Expected Outputs

- `data/processed/cleaned.csv`: Final analysis‑ready dataset.
- `models/best_model.pkl`: Serialized best‑performing model.
- `reports/model_report.json`: Metrics (R², MAE, VIF, power analysis results).
- `reports/shap_summary.png`: Feature importance visualization.

## Troubleshooting

- **`data_schema_mismatch`**: The source dataset lacks required LST columns. Check the `research.md` for verified source content.
- **`data_insufficiency_error`**: Fewer than 100 records found. The study scope is reduced to "pilot" or halted.
- **`runtime_timeout`**: Pipeline exceeded the planned duration. Reduce grid search size or sample size in `train.py`.
- **`raw_subset_invalid`**: The raw subset failed Shapiro‑Wilk or Levene's tests. Sensitivity analysis skipped.
