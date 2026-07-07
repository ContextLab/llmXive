# Quickstart: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

## 1. Prerequisites

- **Python**: 3.11+
- **API Keys**:
  - Materials Project API Key (set as `MP_API_KEY` env var).
  - OQMD Access (if required, otherwise public).
- **Compute**: Standard CPU environment (GitHub Actions free-tier compatible).

## 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-443-predicting-the-effect-of-alloying-on-the

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## 3. Configuration

1.  **Set API Keys**:
    ```bash
    export MP_API_KEY="your-materials-project-key"
    ```
2.  **Verify Paths**: Ensure `data/` and `results/` directories exist.

## 4. Running the Pipeline

### Full Pipeline (Fetch, Train, Evaluate)
```bash
python code/main.py
```
*This script performs:*
1.  Data fetch (API or OQMD CSV fallback).
2.  Feature engineering (ILR, descriptors).
3.  Model training (RF, GB, EN).
4.  Evaluation (Bootstrap, FDR, Sensitivity).
5.  Report generation.

### Individual Steps
- **Fetch Data**: `python code/data/fetch_hea.py`
- **Preprocess**: `python code/data/preprocess.py`
- **Train Models**: `python code/models/train.py`
- **Evaluate**: `python code/models/evaluate.py`

## 5. Output Artifacts

- `data/processed/hea_samples_ilr.parquet`: Processed dataset.
- `results/metrics.yaml`: Performance metrics and confidence intervals.
- `results/figures/parity_plot.png`: Model vs. Observed plot.
- `results/figures/shap_summary.png`: Feature importance.
- `report.md`: Final associational report with disclaimer.

## 6. Troubleshooting

- **Dataset Insufficient**: If the pipeline halts with "Retrieved [N] samples; threshold 500 not met", verify API keys or OQMD CSV content.
- **Memory Error**: If RAM exceeds 7 GB, reduce the dataset size or use `float32` explicitly.
- **API Timeout**: The script includes retry logic with a limited number of attempts. If it fails, check network connectivity.

## 7. Reproducibility

To reproduce results exactly:
1.  Pin random seeds in `code/main.py` (default `42`).
2.  Ensure `data/source_metadata.yaml` matches the run parameters.
3.  Re-run `python code/main.py` from a clean environment.
