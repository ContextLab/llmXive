# Quickstart: Running the Data‑Cleaning Impact Pipeline

These instructions assume a fresh GitHub Actions runner (or local Linux environment) with internet access.

## 1. Setup Environment
```bash
# Clone the repository (already present in CI)
git clone https://github.com/your-org/quantifying-data-cleaning.git
cd quantifying-data-cleaning

# Create a virtualenv and install pinned dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r code/requirements.txt
```

## 2. Verify Dataset Checksums (optional but recommended)
```bash
python code/data_loader.py --verify-only
# Exits with 0 if all SHA‑256 hashes match the values stored in
# state/projects/PROJ-256-...yaml
```

## 3. Run the Full Pipeline
```bash
python src/main.py \
  --seed 42 \
  --bootstrap-iterations 1000 \
  --outlier-ks 1.5 2.0 \
  --permutations 1000
```
The script will:
1. Download the **four** verified datasets (Stepkids, Wine Quality, Breast Cancer, FPR JSONL) and the two auxiliary numeric‑only datasets used for IQR verification.
2. Perform baseline analyses **after assumption checks** (normality, homoscedasticity, linearity) and write results to `data/processed/baseline_metrics.json`.
3. Apply each cleaning variant (outlier removal, imputation, recoding) and capture cleaning metadata (`rows_removed`, `missing_before`, `missing_after`, `variance_reduction`).
4. Re‑run the same statistical tests on each cleaned variant, writing to `data/processed/cleaned_metrics.json`.
5. Sweep outlier thresholds (`k=1.5, 2.0`) and compute false‑positive‑rate via permutation of the documented outcome column, storing results in `data/processed/null_fpr_metrics.json`.
6. Produce bootstrap confidence intervals (≥ 1000 iterations) and add `delta_ci_low` / `delta_ci_high` to the JSON records.
7. Generate static PNG figures (forest plot, heatmap) under `output/figures/`.

## 4. Validate Outputs (Contract Tests)
```bash
pytest -q tests/contract/
```
All tests should pass, confirming that the JSON files conform to the schemas in `contracts/`.

## 5. Inspect Results
```bash
# Pretty‑print JSON (requires jq)
jq . data/processed/baseline_metrics.json | less
jq . data/processed/cleaned_metrics.json | less
jq . data/processed/null_fpr_metrics.json | less

# View figures
display output/figures/forest_plot.png
display output/figures/fpr_heatmap.png
```

## 6. Debug / Subset Run (for faster local testing)
```bash
python src/main.py --sample-datasets 1 --bootstrap-iterations 200 --permutations 200
```
This respects the same code paths but reduces compute; the contract tests will still verify schema compliance.

## 7. No Fabricated Metrics
The pipeline **must** generate all metric files (`baseline_metrics.json`, `cleaned_metrics.json`, `null_fpr_metrics.json`) from real computations on the downloaded datasets. If any required metric is missing, NaN, or hard‑coded, the run will abort with an error, ensuring that no fabricated results reach the final report.
