# Quickstart: Predicting the Impact of Impurities on the Superconductivity of Magnesium Diboride

## Prerequisites

- Python 3.11+
- Git
- Access to the internet (for downloading datasets)
- (Required for MP data) Materials Project API Key (set `MATERIALS_PROJECT_API_KEY` env var)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-276-predicting-the-impact-of-impurities-on-t
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via `main.py` in the `code/` directory.

```bash
cd code/
python main.py
```

### Steps Executed

1.  **Ingestion**: Downloads data from `taqwa92/cm.mgb2` and (optionally) Materials Project API.
    - *Note*: If `MATERIALS_PROJECT_API_KEY` is not set, MP data is skipped.
2.  **Preprocessing**: Cleans, converts units, and saves `data/processed/mgb2_clean.csv`.
3.  **Training**: Trains Linear, RF, and XGBoost models. Saves `data/processed/model_results.json`.
4.  **Evaluation**: Runs significance tests and generates Partial Dependence Plots. Saves figures to `data/processed/plots/`.

## Verifying Results

- **Check Data**: Ensure `data/processed/mgb2_clean.csv` exists and contains non-null `tc_k` and `impurities`.
- **Check Models**: Verify `data/processed/model_results.json` contains R² scores for all three models.
- **Check Plots**: Look for `pdp_top3_impurities.png` in `data/processed/plots/`.
- **Check Significance**: Confirm `data/processed/impurity_effects.json` lists elements with $p < 0.05$.

## Troubleshooting

- **Error: "No verified source found"**: The script cannot find the Materials Project API. It will proceed with the SuperCon dataset only. If SuperCon data is also missing, the script exits with code 1.
- **Error: "Memory limit exceeded"**: Reduce the `max_depth` of XGBoost or the number of trees in the grid search in `config.yaml`.
- **Error: "Collinearity detected"**: The script will automatically flag collinear features but retain them using Ridge Regression. Check the logs for which features were affected.
- **Error: "Sample size too small"**: The combined dataset has fewer than 100 entries. Please verify data sources or API keys.
- **Error: "Impurity parsing failed"**: The dataset lacks structured impurity columns and text parsing failed. Check the source data format.