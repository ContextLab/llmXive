# Quickstart: Detecting Statistical Power Drift in Replicated Studies

## Prerequisites
- Python 3.11+
- `pip`
- GB+ RAM available

## Installation

1. **Clone the repository** (if not already done).
2. **Install dependencies**:
   ```bash
   cd code
   pip install -r requirements.txt
   ```
   *Dependencies*: `pandas`, `statsmodels`, `scipy`, `matplotlib`, `pyyaml`, `datasets`, `pytest`.

## Data Download

The pipeline automatically downloads the OSF dataset from HuggingFace upon first run. To download manually:
```bash
python download_data.py
```
This will create `data/raw/` with the verified parquet/CSV files and generate checksums.

## Running the Analysis

Execute the full pipeline:
```bash
python -m code.run_pipeline
```
This script orchestrates:
1. Data download and validation.
2. Power calculation.
3. Residualization and LMM/GLMM fitting and LRT.
4. Permutation test (sufficient iterations for convergence).
5. Sensitivity analysis (calculating FPR from null distribution).
6. Input Permutation test.
7. Visualization generation.

**Expected Runtime**: ~1-2 hours on a standard CPU (well within the specified time limit).

## Output Artifacts

- `data/derived/power_estimates.csv`: Calculated power for each study.
- `data/derived/residuals.csv`: Residuals for plotting.
- `data/derived/schema_validation.json`: Validation report (T007).
- `results/power_drift_scatter.png`: The primary visualization (residual power vs. year).
- `results/robustness_summary.json`: Permutation p-values, sensitivity results (including FPR), and input permutation results.

## Verification

To verify the results:
```bash
pytest tests/
```
This runs unit tests for power formulas and integration tests ensuring the pipeline produces the expected output files.