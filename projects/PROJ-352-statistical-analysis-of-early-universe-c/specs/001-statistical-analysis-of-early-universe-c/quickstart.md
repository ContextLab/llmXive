# Quickstart: Running the CMB Minkowski Functional Analysis

These instructions assume a fresh GitHub Actions runner or a local Linux/macOS environment with at least 2 CPU cores and 7 GB RAM.

## 1. Clone the Repository
```bash
git clone https://github.com/your-org/early-universe-cmb-defect.git
cd early-universe-cmb-defect
```

## 2. Set Up a Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install Exact Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
*All versions are pinned; no GPU libraries are installed.*

## 4. Run the Full Pipeline
```bash
python -m src.pipeline \
  --planck-url https://pla.esac.esa.int/pla/aio/product-action?product=COM_CMB_SMICA_2048_R3.00_full.fits \
  --mask-url   https://pla.esac.esa.int/pla/aio/product-action?product=COM_Mask_Galactic_2048_R3.00.fits \
  --pspec-url  https://pla.esac.esa.int/pla/aio/product-action?product=COM_PowerSpectra_TT_plikHMv18_TT_lowTEB_lmax5000_R3.00.fits \
  --nside 128 \
  --seed 42 \
  --sim-count 1000 \
  --thresholds "-1.0 -0.5 0.0 0.5 1.0"
```
The command will:
1. Download the SMICA map and mask (with retries).  
2. Apply the mask (2‑pixel buffer).  
3. Compute observed Minkowski Functionals using `pyminkowski`.  
4. Generate **exactly** 1 000 Gaussian simulations (no fallback).  
5. Compute functionals for each simulation, estimate covariance, run Hotelling’s T² test, and write all artifacts.

## 5. Inspect Results
```bash
# Basic summary
cat report.md

# View the Hotelling test JSON
jq '.' data/processed/hotelling_result.json

# Plot of observed vs. simulation MF curves (requires matplotlib)
python -c "import matplotlib.pyplot as plt, pandas as pd; \
obs = pd.read_csv('data/processed/minkowski_observed.csv'); \
sims = pd.read_csv('data/processed/minkowski_sims.csv'); \
plt.plot(obs['threshold'], obs['genus'], label='Observed'); \
plt.plot(sims['threshold'].unique(), sims.groupby('threshold')['genus'].mean(), label='Simulated mean'); \
plt.legend(); plt.savefig('figures/mf_comparison.png')"
```

## 6. Run the Test Suite (optional)
```bash
pytest -v
```
All tests should pass, confirming checksum validation, reproducibility, and that acceptance criteria (coverage, precision, p‑value format) are met.

## 7. Resource Limits
The pipeline monitors RAM usage. **If RAM usage exceeds 6.5 GB or any phase cannot finish within the allotted time, the job aborts with a non‑zero exit code** and no partial results are written. This guarantees compliance with the GitHub Actions free‑tier limits (Principle VII) and preserves statistical integrity.

---

