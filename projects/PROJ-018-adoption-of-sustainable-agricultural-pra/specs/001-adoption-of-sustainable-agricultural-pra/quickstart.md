# Quickstart: Adoption of Sustainable Agricultural Practices in Low‑Income Areas through Community Engagement

## Prerequisites

- Python 3.11+
- pip / virtualenv
- 2 CPU cores, 7 GB RAM (GitHub Actions Free Tier compatible)
- **Minimum 500 observations for stable mediation bootstrap estimates (documented limitation if below)**

## Installation

1.  **Clone Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-018-adoption-of-sustainable-agricultural-pra
    ```

2.  **Setup Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

### Option A: CI / Synthetic Data (Default)
Runs the full pipeline using synthetic data conforming to the schema.
```bash
python code/01_download_data.py --synthetic
python code/02_clean_data.py
python code/03_engineer_features.py
python code/04_model_analysis.py
python code/05_generate_report.py
```
*Output*: `results/final_report.pdf`, `results/model_results.json`.

### Option B: Real Data (Manual)
1.  Download LSMS/FAO FIES microdata (Note: No verified URL exists in project block).
2.  Place raw file in `data/raw/survey_data.csv`.
3.  Run pipeline (skips download step):
    ```bash
    python code/02_clean_data.py --input data/raw/survey_data.csv
    ... (rest of steps)
    ```

## Verification

- **Data Check**: Ensure `data/processed/cleaned_survey_data.csv` exists.
- **Model Check**: Ensure `results/model_results.json` contains `auc`, `vif_scores`, `fdr_adjusted_p`, `correlation_matrix`, `efa_loadings`, `mediation_sensitivity`.
- **Report Check**: Open `results/final_report.pdf` to verify tables, plots, and sensitivity analysis results.

## Troubleshooting

- **Memory Error**: Reduce synthetic sample size in `code/01_download_data.py`.
- **Missing Variables**: Check `data/metadata.yaml` for schema compliance (all 4 engagement items required per `contracts/dataset.schema.yaml`).
- **VIF Warning**: Check `results/model_results.json` for VIF ≥ 5; consider removing collinear predictors.
- **Correlation Warning**: Check `results/model_results.json` for pairwise correlations > 0.70; interpret effects descriptively.
- **Mediation Power**: If N < 500, mediation bootstrap estimates may be unstable; limitation documented in report.