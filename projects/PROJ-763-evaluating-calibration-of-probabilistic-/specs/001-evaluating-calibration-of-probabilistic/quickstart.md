# Quickstart: Evaluating Calibration of Probabilistic Weather Forecasts

## Prerequisites
- Python 3.11+
- `git`
- Access to a GitHub Actions runner (or local environment with 7 GB+ RAM).
- Network access to download the SubseasonalRodeo dataset.

## Installation

1. **Clone the repository** (if applicable) or navigate to the project directory.
   ```bash
   cd projects/PROJ-763-evaluating-calibration-of-probabilistic-
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` will pin versions for `pandas`, `numpy`, `scikit-learn`, `properscoring`, `pymc`, `arviz`, `matplotlib`, `seaborn`, `tqdm`, `statsmodels`.*

## Data Acquisition

The pipeline requires the `SubseasonalRodeo` dataset.

1. **Run the download script**:
   ```bash
   python code/src/download.py
   ```
   - This script attempts to download the dataset via `wget` from the canonical source (GitHub Release or Zenodo).
   - It verifies the checksum.
   - **If download fails**: The script exits with an error "Dataset acquisition failed". Do not proceed.

2. **Verify data**:
   Ensure `data/raw/` contains the expected files (e.g., `subseasonal_rodeo.parquet` or similar).

## Running the Pipeline

Execute the full pipeline (Baseline -> Isotonic -> Bayesian -> Comparison):

```bash
python code/main.py
```

### Steps Performed:
1. **Download & Verify**: (Skipped if data exists and checksum matches).
2. **Align**: Joins forecasts and observations, discards missing data.
3. **Baseline**: Computes Brier/CRPS and generates `reliability_diagram_raw.png`.
4. **Isotonic**: Fits isotonic regression, computes metrics, generates `reliability_diagram_isotonic.png`.
5. **Bayesian**: Runs MCMC (scaled, stratified sample), computes metrics, checks convergence.
6. **Comparison**: Runs Diebold-Mariano / Wilcoxon tests (per FR-006).
7. **Output**: Saves all results to `results/`.

## Expected Outputs

After successful completion, the `results/` directory will contain:

- `results_baseline.csv`: Baseline metrics (Brier, CRPS) per lead time.
- `results_isotonic.csv`: Isotonic recalibration metrics.
- `results_bayesian.csv`: Bayesian recalibration metrics (includes `convergence_status`).
- `reliability_diagram_raw.png`: Baseline reliability diagram.
- `reliability_diagram_isotonic.png`: Isotonic reliability diagram.
- `comparison_summary.csv`: Results of statistical tests (DM/Wilcoxon).

## Troubleshooting

- **Dataset Download Failed**:
  - Check network connectivity.
  - Verify the canonical URL for SubseasonalRodeo is still active.
  - If the dataset is gated, the pipeline cannot proceed without manual data provision (which violates the "open data" constraint).

- **Bayesian Convergence Failed**:
  - Check `results/results_bayesian.csv` for `convergence_status = "Unconverged"`.
  - This may happen if the sample size is too small or the model is too complex for the data. The pipeline will fall back to Isotonic results.

- **Out of Memory (OOM)**:
  - If the dataset is too large, the script uses chunked reading. If OOM persists, reduce the `SAMPLE_SIZE` constant in `code/src/recalibrate_bayesian.py` (for the Bayesian step only).

## Validation

Run contract tests to ensure output schemas are valid:

```bash
pytest tests/contract/
```

This validates that all CSVs match the schemas defined in `contracts/`.