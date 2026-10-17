# Quickstart: Predicting the Impact of Impurity Clustering on Grain Boundary Segregation

## Prerequisites
- Python 3.11 or newer
- `git` and internet access (to fetch OQMD data from HuggingFace)
- Optional: Materials Project bulk mirror URL (no API key needed)

## Installation
```bash
git clone https://github.com/your-org/PROJ-355-predicting-the-impact-of-impurity-cluste.git
cd PROJ-355-predicting-the-impact-of-impurity-cluste
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Generate Documentation (verifies T001b & T001c)
```bash
python -m code.generate_docs
```
- Creates a `.gitignore` containing exactly:
  ```
  data/
  results/
  __pycache__/
  *.pyc
  ```
- Creates a `README.md` with the required sections:
  - Project title
  - Execution instructions (as shown here)
  - Data provenance section that cites the OQMD and Materials Project mirror URLs.

## Step‑by‑Step Pipeline

### 1. Run Full Analysis
```bash
python -m code.main --mode full
```
This command sequentially:
1. Downloads bulk structures from OQMD (fallback to the verified MP mirror).  
2. Builds GB supercells and inserts impurities at the interface.  
3. Computes RDF peaks, pair‑correlation, and Voronoi counts **only** at the interface.  
4. Simulates segregation energies with the NIST Fe‑Cr EAM potential (CPU‑tractable) and performs an **optional sanity‑check validation** against a public DFT benchmark (≥100 structures, MAE ≤ 0.05 eV).  
5. Assembles the training set and writes `data/processed/training_set.csv` (validated against the dataset schema).  
6. Trains a **Ridge regression** model with 5‑fold CV (or LOOCV if N < 5) and conducts a power analysis (required_n = 200, achieved_n logged, achieved_power computed).  
7. Applies Bonferroni or Benjamini‑Hochberg correction to coefficient p‑values.  
8. Performs a λ‑sweep (25th, 50th, 75th percentiles) and records RMSE variance & R² stability.  
9. Writes `results/metrics.json` and `results/sensitivity.json` (validated against the output schema).

### 2. Inspect Results
```bash
cat results/metrics.json
cat results/sensitivity.json
```

## CI Execution
The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs:
```bash
python -m code.main --mode ci
```
- Uses a reduced sample size (`--sample-size <adequate sample size>`) to stay within the 6‑hour, A modest RAM limit (e.g., on the order of several gigabytes)..
- All artifacts are automatically checked against the JSON schemas.

## Troubleshooting
| Symptom | Fix |
|---------|-----|
| `[DATA_UNAVAILABLE]` after 3 retries | Verify network connectivity; check the HuggingFace URLs listed in the plan. |
| Simulation fails repeatedly | Ensure `FeCr.eam.fs` is present in `code/` and that `ASE` is installed. |
| VIF ≥ 10 warnings | Review the `descriptive_framing` field in `results/metrics.json`; no model changes needed. |
| Optional validation aborts (MAE > 0.05 eV) | Check that the DFT benchmark file downloaded correctly; re‑run the full mode. |
| CI times out | Reduce `--sample-size` or increase the `--max-retries` parameter in `download.py`. |

## Expected Outputs
- `data/processed/training_set.csv` – final regression dataset (schema‑validated).  
- `results/metrics.json` – model performance, raw/adjusted p‑values, VIF scores, collinearity framing, and power‑analysis fields.  
- `results/sensitivity.json` – RMSE variance & R² stability across λ thresholds.  
- `.gitignore` & `README.md` – verifiable artifacts for T001b/T001c.
