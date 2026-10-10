# Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

This project quantifies the extent to which residual stress mediates the
relationship between manufacturing process parameters and fatigue life across
material classes (steels vs. aluminum alloys), and measures how much predictive
value stress-mediated estimation adds beyond direct process-to-fatigue modeling.

## Project overview

1. **Ingestion** — public fatigue datasets (NIST, UCI, OpenML) are downloaded from
 canonical, version-pinned URLs; per-row SHA-256 checksums are recorded; stress
 units are standardized to MPa; missing numeric values are median-imputed; and a
 residual-stress proxy `σ_res = k·heat_input·cooling_rate` (k = 0.8 steel,
 k = 0.6 aluminum) is computed where measured values are absent and flagged
 (`is_proxy=True`), with negatives clamped to 0.01 MPa.
2. **Feature sets** — A (process only), B (process + measured residual stress),
 C (process + material properties).
3. **Models** — RandomForest, GradientBoosting, and a shallow PyTorch NN,
 selected via stratified 5-fold CV with a fixed seed (SEED=42).
4. **Evaluation** — MAPE/R² overall and per material class, paired t-tests with
 Bonferroni correction, cross-material transfer evaluation, and bootstrap
 mediation analysis (10,000 resamples) on the measured-stress subset only.
5. **Reporting** — tables and figures under `results/`, plus a reproducibility
 report.

## How to obtain raw data

Raw data is downloaded automatically by the ingestion script
(`code/ingest/ingest.py`) from the canonical URLs recorded in its
`DATASET_URLS` mapping and stored under `data/raw/`. No manual download is
required. Each source file's provenance is captured via per-row SHA-256
checksums stored in the `checksum` column of
`data/processed/unified_fatigue.csv`.

## Quick start

```bash
python -m venv.venv
source.venv/bin/activate
pip install -r requirements.txt
make env-check # verify all pinned dependencies import correctly
bash run_pipeline.sh # run the full analysis end-to-end
```

See `quickstart.md` for the detailed run book.

## Reproducibility

- All random seeds are fixed (`SEED=42`) for data splits, model initialization,
 and bootstrap resampling.
- Dependency versions are pinned in `requirements.txt`.
- `make env-check` verifies the environment and writes `results/env_check.log`.
- The pipeline respects the GitHub Actions free-tier limits (≤ 6 h, ≤ 7 GB RAM).

## Repository layout

```
code/ analysis modules (ingest, features, models, eval, mediation, report)
data/ raw and processed datasets
results/ performance tables, figures, and verification logs
tests/ pytest suite
specs/ feature specification and data contracts
```