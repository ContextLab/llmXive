# Quickstart: Statistical Properties of Integer Partitions Into Distinct Prime Summands

## Prerequisites
- Python 3.11 or newer
- Git
- Internet access (to clone the repository)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/PROJ-799-statistical-properties-of-integer-partit

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install pinned dependencies
pip install -r requirements.txt
```

## Running the Full Pipeline

```bash
python code/main.py
```

The script executes the steps in order:

1. Generate primes up to 50 000 (if not already present).  
2. Compute exact partition counts `p_P_n` (DP).  
3. Compute the calibrated **numerical saddle‑point** asymptotic `Q_as_n`.  
4. Engineer density features and log‑residuals, producing `data/processed/features.csv`.  
5. Fit the regression model (OLS with optional ridge, null model, BH correction, HAC SE).  
6. Save `model_results.json` and the diagnostic plot `residuals_plot.png`.

All intermediate artifacts are written under `data/processed/`.

## Running Individual Steps

| Step | Command | Output |
|------|---------|--------|
| Prime sieve | `python code/generate_primes.py` | `data/raw/primes_up_to_50000.csv` |
| Partition counts | `python code/generate_partitions.py` | `data/processed/partition_counts.csv` |
| Asymptotic baseline | `python code/compute_baseline.py` | `data/processed/baseline_values.csv` |
| Feature engineering | `python code/feature_engineering.py` | `data/processed/features.csv` |
| Model fitting | `python code/fit_model.py` | `data/processed/model_results.json` |
| Visualization | `python code/visualize.py` | `data/processed/residuals_plot.png` |

## Verification

```bash
pytest tests/ -v
```

Key tests:

- `test_dp_logic.py` – checks DP counts for \(n=5,6,10\) against known values.  
- `test_features_non_null.py` – asserts **no missing values** in the columns used for regression (`pi_n`, `inv_log_n`, `cum_density`, `gap_n`).  
- `test_baseline.py` – validates that the asymptotic formula produces positive values and respects the clamping rule.  
- `test_schema_contracts.py` – runs JSON‑schema validation against all `contracts/*.schema.yaml`.  

## Expected Outputs

- `data/processed/features.csv` – full dataset (≈ tens of thousands of rows) with required columns.  
- `data/processed/model_results.json` – regression coefficients, \(R^{2}\), FDR‑adjusted \(p\)‑values, CV MSE, and null‑model statistics.  
- `data/processed/residuals_plot.png` – visual comparison of raw residuals and fitted correction term.  

All files are checksum‑tracked for reproducibility.


