# Quickstart: Predictive‑Coding Cross‑Illusion Analysis

These commands assume a fresh GitHub Actions runner (or a local Linux environment with Python 3.11).

## 1. Setup the Environment
```bash
# Navigate to the project root (already checked out in CI)
cd projects/PROJ-406-investigating-neural-signatures-of-predi

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r requirements.txt
```

## 2. Verify Deterministic Seeding (Reproducibility)
```bash
python -c "from src.utils.seed import set_global_seed; set_global_seed(42); \
import numpy as np; print('First draw:', np.random.rand()); \
set_global_seed(42); print('Second draw (should match):', np.random.rand())"
# The two printed numbers must be identical; this log is used by the verifier for reproducibility.
```

## 3. Download & Verify Datasets
```bash
python -m src.ingest.load_illusions \
    --download \
    --output-dir data/raw
# The script:
#   * downloads the two OpenNeuro parquet files from the verified URLs,
#   * computes SHA‑256 checksums,
#   * aborts with a clear error if a checksum mismatches or a file is missing.
```

## 4. Clean the Data
```bash
python -m src.ingest.load_illusions \
    --clean \
    --raw-dir data/raw \
    --clean-dir data/clean
# Produces:
#   data/clean/clean_muller_lyer.csv
#   data/clean/clean_ponzo.csv
# The script logs how many rows were dropped due to missing responses.
```

## 5. Fit the Hierarchical Predictive‑Coding Model (Training)
```bash
python -m src.model.predictive_coding \
    --input data/clean/clean_muller_lyer.csv \
    --output data/derived/precision_parameters.csv \
    --seed 42
# Outputs per‑subject λ, log‑likelihood, AIC, BIC.
```

## 6. Compute Ponzo Susceptibility Scores (Test)
```bash
python -m src.analysis.null_model \
    --input data/clean/clean_ponzo.csv \
    --output data/derived/ponzo_susceptibility.csv \
    --seed 42
# Outputs per‑subject β and model R².
```

## 7. Cross‑Illusion Prediction & Validation
```bash
python -m src.analysis.correlation \
    --precision data/derived/precision_parameters.csv \
    --susceptibility data/derived/ponzo_susceptibility.csv \
    --results outputs/correlation_results.json \
    --fig-dir outputs/figures \
    --bootstrap 1000 \
    --permute 1000 \
    --seed 42
# Generates:
#   - correlation_results.json (r, p, CI, N, linearity_check_passed flag)
#   - outputs/figures/scatter.png
#   - outputs/figures/bootstrap_hist.png
#   - outputs/figures/fit_residuals.png
# If the paired sample size is below the power‑analysis requirement, the script aborts and falls back to a Bayesian correlation estimate (reported in the JSON).
```

## 8. Verify Contracts
```bash
# Install jsonschema for contract validation
pip install jsonschema==4.22.*

# Example validation (repeat for each schema)
python - <<'PY'
import json, csv, yaml, jsonschema, pathlib
def csv_to_records(path):
    with open(path, newline='') as f:
        return [row for row in csv.DictReader(f)]
# Validate merged results
schema = yaml.safe_load(open('contracts/merged-results.schema.yaml'))
data   = csv_to_records('data/merged/merged_results.csv')
jsonschema.validate(instance=data, schema=schema)
PY
```
(Implementations already include automated contract checks; the command above is for manual inspection.)

## 9. Inspect Results
- Open `outputs/correlation_results.json` to see the correlation coefficient, p‑value, 95 % CI, and the linearity‑check flag.  
- View the PNGs in `outputs/figures/` for visual diagnostics.  

## 10. Clean Re‑run (optional)
```bash
rm -rf data/clean data/derived outputs
# Then repeat steps 4‑7.
```

All steps are fully deterministic (seeded), verified via checksums, and respect the 6‑hour CI runtime limit.

---

