# Quickstart: The Impact of Simulated Social Comparison on Self-Evaluation in Online Environments

This guide walks a new researcher from a fresh GitHub Actions runner to a complete PDF report.

## 1️⃣ Setup
```bash
# Clone the repo (already done in CI)
cd projects/PROJ-389-the-impact-of-simulated-social-compariso

# Create virtualenv and install pinned deps
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2️⃣ Data Download & Pre‑processing
```bash
python -m src.ingest.reddit_ingest \
    --streaming \
    --output data/raw_user_comments.parquet
```
- Streams the Pushshift Reddit dump, removes PII, aggregates per user.

## 3️⃣ Feature Extraction
```bash
python -m src.features.extract_features \
    --input data/raw_user_comments.parquet \
    --subreddit-metadata data/subreddit_metadata.parquet \
    --output data/processed_features.csv \
    --seed 42
```
- Generates all predictor columns **and** the additional covariates (total comment count, subreddit popularity score, month of activity).  
- **Important**: `exposure_level` is computed from **subreddit‑wide metadata** (distinct from the user’s own comment stream), while `self_eval_score` is computed **only from the user’s own comments**, satisfying Principle VI.  
- Logs low‑variance skips, median‑imputes any residual missing values, and writes a `notes` column.  

## 4️⃣ Power Check (optional)
```bash
python -m src.utils.power_check \
    --features data/processed_features.csv \
    --target_n 500 \
    --effect_size 0.15
```
- Reports whether each demographic subgroup meets the ≥ 500 sample‑size requirement; logs a power‑limitation warning if not.

## 5️⃣ Regression & Diagnostics
```bash
python -m src.analysis.moderation_regression \
    --features data/processed_features.csv \
    --results data/regression_results.csv \
    --seed 42
```
- Fits hierarchical models, computes VIF, applies Benjamini‑Hochberg FDR, writes results conforming to `contracts/regression_results.schema.yaml`.

## 6️⃣ Demographic Stratification & Plots
```bash
python -m src.viz.demographic_plots \
    --results data/regression_results.csv \
    --output reports/interaction_plots.pdf
```
- Produces interaction plots for each subgroup **with ≥ 500 users**; if demographic proxies are insufficient, the script falls back to a global plot and notes the limitation.

## 7️⃣ Sensitivity Analysis (optional)
```bash
python -m src.analysis.sensitivity_sweep \
    --features data/processed_features.csv \
    --output reports/sensitivity_summary.csv
```
- Sweeps self‑reference and sentiment thresholds ±0.05 and reports variation in headline moderation effect sizes.

## 8️⃣ Verify Contracts
```bash
pytest -q tests/contract/test_regression_schema.py
```
- Ensures `regression_results.csv` matches the JSON‑Schema contract.

## 9️⃣ Final Report
All artifacts are now in `reports/`. Open `reports/interaction_plots.pdf` and `reports/sensitivity_summary.csv` for the complete results.

**All steps complete within the CI runner limits** (≤ 6 h, ≤ 6 GB RAM).

---

