# Quickstart: Predicting the Ductility of Additively Manufactured Nickel-Based Superalloys

## Prerequisites

- Python 3.11+
- `pip`
- Access to GitHub Actions runner (for CI execution) or local environment.
- **Data Access**: You must manually provide the supplementary tables from the four cited papers (PDF/Excel) in `data/raw/` or update `acquisition.py` with the correct parsing logic for the specific papers.

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r code/requirements.txt
    ```

## Data Acquisition

The system relies on **Literature Synthesis** (parsing paper tables) as no verified HF dataset is available.

```bash
# Place paper tables in data/raw/
python code/data/acquisition.py --parse-papers
```

*Note: If you have the actual CSV files from the cited papers, place them in `data/raw/` and run `python code/data/acquisition.py --load-local`.*

## Running the Pipeline

Execute the full pipeline (cleaning, modeling, reporting):

```bash
python code/main.py
```

This will:
1.  Clean and engineer features (including Composition Mapping).
2.  Run VIF analysis and select the appropriate feature set (Components or Energy Density).
3.  Fit the Linear Mixed-Effects model (with bootstrapping for small N).
4.  Train the XGBoost regressor using **Leave-One-Alloy-Family-Out** CV.
5.  Generate `final_report.md` with **Partial Dependence Plots** in `artifacts/`.

## Verification

Check the output logs for:
- `VIF Check`: Ensure max VIF ≤ 5.
- `Model Convergence`: LME model must converge.
- `Metrics`: Mean CV R², MAE, RMSE for XGBoost.
- `Report`: Verify PDPs are generated for the top 3 features.

## Troubleshooting

- **VIF > 5**: The script automatically switches to Energy Density-only model. Check `logs/vif_log.txt`.
- **Model Non-Convergence**: If LME fails, check for singular matrices in `data/processed_build_records.csv`.
- **Time Out**: If XGBoost takes > 600s, reduce `n_estimators` in `code/models/xgboost_model.py`.
