# Quickstart: Exploring the Correlation Between Musical Preference and Personality Traits

This guide walks you through running the full analysis pipeline on a fresh GitHub Actions runner (or locally) using the provided code and, for testing purposes, a synthetic placeholder dataset.

## Prerequisites
- Python 3.11
- Git
- Internet access (to download the BFI‑2 dataset)

## Setup

```bash
# Clone the repository (assumes you are in the project root)
git clone https://github.com/your-org/your-repo.git
cd your-repo

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Step‑by‑Step Execution

1. **Download & Prepare Data**

```bash
# Fetch the verified BFI‑2 dataset
python -m src.ingest.download   # aborts if a real linked Last.fm dataset is not available

# OPTIONAL: generate synthetic Last.fm data for CI testing only
python -m src.synthetic_data     # writes data/raw/lastfm_synthetic.parquet and data/processed/synthetic_data.csv

# Clean, merge, map genres, compute totals, and impute missing demographics
python -m src.ingest.preprocess
# Output: data/processed/merged_dataset.csv
```

2. **Power Analysis (hard abort if under‑powered)**

```bash
python -m src.analysis.power_analysis
# Logs required N ≈ a sufficiently large sample size; aborts if actual N < required.
```

3. **Correlation Computation (with diagnostics & fallback)**

```bash
python -m src.analysis.correlations
# Produces data/processed/analysis_results.csv
# Includes diagnostic logs; uses Spearman if Pearson assumptions fail.
```

4. **Fit Regression Models & Compute Coefficient Deltas**

```bash
python -m src.analysis.regressions
# Uses raw listening_minutes as predictors + covariates (age, gender, country, total_minutes)
# Generates:
#   data/processed/analysis_results.csv   (beta, SE, etc.)
#   data/processed/coefficient_deltas.csv
```

5. **Generate Visualizations & Report**

```bash
python -m src.reporting.visualizations   # creates results/correlation_heatmap.png
python -m src.reporting.report           # creates results/results_report.csv
```

6. **Validate Contracts**

```bash
python -m src.utils.validate_contracts
# Validates merged_dataset.csv, analysis_results.csv, coefficient_deltas.csv,
# and results_report.csv against their respective schemas.
# Exits with non‑zero status on any mismatch.
```

7. **Run Tests (CI style)**

```bash
pytest -vv
```

## Expected Outputs
- `data/processed/merged_dataset.csv` – cleaned, merged data (validated).  
- `data/processed/analysis_results.csv` – full statistical table (correlations, regressions).  
- `data/processed/coefficient_deltas.csv` – delta analysis for regression coefficients.  
- `results/correlation_heatmap.png` – heatmap of correlation matrix.  
- `results/results_report.csv` – CSV with Cohen’s d, 95 % CI, and explicit significance labels.  

**Important**: The synthetic data generated in step 1 is **only** for pipeline verification. For any scientific conclusion, a genuine, consented linked BFI‑2 + Last.fm dataset must be supplied; otherwise the pipeline aborts per FR‑001.

---

