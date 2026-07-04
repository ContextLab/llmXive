# Quickstart: Predicting the Impact of Composition on the Glass Transition Temperature of Chalcogenide Glasses

## Prerequisites

- Python 3.11+
- `pip` or `conda`
- Access to a GitHub Actions runner (or local machine with similar constraints).

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins versions for reproducibility.*

## Data Setup

1. **Download Dataset**:
   Run the download script. It will attempt to fetch from the documented URL in the spec (arXiv:2211.00691v1 supplementary).
   ```bash
   python src/data/download.py
   ```
   *If the URL fails, the script retries 3 times and logs the error. If the URL is unreachable, it halts with `DATA_MISSING: URL_UNREACHABLE`.*

2. **Verify Data**:
   Check `data/raw/` for the downloaded file. Ensure it contains `composition` and `Tg` columns.

## Running the Pipeline

Execute the full pipeline:
```bash
python src/main.py
```

This will:
1. **Preprocess**: Compute MCN, $\sigma_{\chi}$, $\sigma_{r}$.
2. **Power Analysis**: Estimate MDES and flag power limitations.
3. **Split**: Stratified train/test split (80/20) or **LOFO** if strata are small (<10 samples).
4. **Train**: Train GBR and Linear models with 5-fold CV.
5. **Evaluate**: Compute RMSE, R², VIF.
6. **Mitigate**: If VIF > 5, apply **Residualization** (orthogonalization).
7. **Explain**: Generate SHAP analysis (with sampling if needed), **Cross-Family Transferability Test**, and report.

## Output

- **Metrics**: `artifacts/performance_metrics.json` (includes MDES, Transferability metrics)
- **SHAP Report**: `artifacts/shap_report.md` (includes Causal Disclaimer, Power Limitation note)
- **Plots**: `artifacts/` (feature importance, SHAP summary, Transferability plots).
- **Data Hygiene**: `state/` file with checksums for raw, processed, residualized, and SHAP subset files.

## Troubleshooting

- **Memory Error**: If SHAP fails, the system automatically samples to ≤5000 rows. Check logs for "SHAP_SAMPLING" message.
- **Data Missing**: If required columns are missing, the script halts with "DATA_MISSING: Required column [name] not found".
- **URL Unreachable**: If the dataset URL is not found, the script halts with "DATA_MISSING: URL_UNREACHABLE".
- **Collinearity**: If VIF > 5, the report will flag this in `shap_report.md` and describe the orthogonalization strategy applied.
- **Small Families**: If a chemical family has < 10 samples in the test set, the system automatically switches to LOFO and logs "LOFO_ACTIVATED".