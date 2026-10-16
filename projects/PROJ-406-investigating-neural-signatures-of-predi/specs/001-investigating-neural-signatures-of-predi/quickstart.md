# Quickstart: Predictive‑Coding Cross‑Illusion Analysis

These instructions assume a fresh GitHub Actions runner (or a local Linux environment with Python 3.11).

## 1. Setup
```bash
# Clone the repository (already done in CI)
cd projects/PROJ-406-investigating-neural-signatures-of-predi

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

## 2. Download & Verify Datasets
```bash
python -m src.ingest.load_illusions \
    --download \
    --output-dir data/raw
# The script will:
#   * download the two OpenNeuro parquet files (verified URLs listed in the plan’s “Verified Datasets” block)
#   * compute SHA‑256 checksums and compare to values stored in state/...yaml
#   * abort with a clear message if a checksum mismatches or a file is missing
```

## 3. Clean the Data
```bash
python -m src.ingest.load_illusions \
    --clean \
    --raw-dir data/raw \
    --clean-dir data/clean
# Produces clean_muller_lyer.csv and clean_ponzo.csv
```

## 4. Fit the Predictive‑Coding Model (Training)
```bash
python -m src.model.predictive_coding \
    --input data/clean/clean_muller_lyer.csv \
    --output data/derived/precision_parameters.csv \
    --seed 42
```

## 5. Compute Ponzo Susceptibility Scores (Test)
```bash
python -m src.analysis.null_model \
    --input data/clean/clean_ponzo.csv \
    --output data/derived/ponzo_susceptibility.csv \
    --seed 42
```

## 6. Cross‑Illusion Prediction & Validation
```bash
python -m src.analysis.correlation \
    --precision data/derived/precision_parameters.csv \
    --susceptibility data/derived/ponzo_susceptibility.csv \
    --results outputs/correlation_results.json \
    --fig-dir outputs/figures \
    --bootstrap 1000 \
    --permute 1000 \
    --seed 42
```

## 7. Inspect Results
- Open `outputs/correlation_results.json` for the correlation coefficient, p‑value, and 95 % CI.  
- View figures in `outputs/figures/` (`scatter.png`, `bootstrap_hist.png`, `fit_residuals.png`).  
- All generated files have secure hash (e.g., SHA‑based) checksums recorded automatically; CI will fail if any checksum mismatches.

## 8. Re‑run / Clean Up
```bash
# To re‑run the entire pipeline from scratch:
rm -rf data/clean data/derived outputs
# Then repeat steps 3‑6.
```

**Note:** The pipeline is fully deterministic thanks to the fixed random seeds (`--seed <fixed_value>`). No manual intervention is required beyond optional manual download if the automatic fetch fails (see Edge Cases).

