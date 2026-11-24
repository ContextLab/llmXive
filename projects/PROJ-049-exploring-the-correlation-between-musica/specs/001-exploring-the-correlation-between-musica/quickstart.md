# Quickstart: Correlation Between Musical Preference & Personality (Illustrative)

This guide shows how to run the full analysis on a fresh GitHub Actions runner (or locally) using the **verified BFI‑2 dataset**. Because a verified Last.fm listening‑history dataset is not available, the pipeline will **abort** if the linked dataset cannot be assembled; no synthetic data are generated. When the linked dataset is present, the statistical workflow (Pearson correlations, regressions, diagnostics, visualizations) proceeds exactly as specified.

## 1. Prerequisites
```bash
# Python 3.11 must be installed
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## 2. Directory Layout (auto‑created by the pipeline)
```
data/
├── raw/
│   └── bfi_raw.csv
├── processed/
│   └── processed_dataset.parquet
results/
├── correlation_heatmap.png
├── regression_coefficients.png
├── results_report.csv
├── coefficient_deltas.csv
├── logs/
│   └── pipeline.log
```

*Note*: The pipeline creates the above directories and also places empty `__init__.py` files in `src/` and `tests/` to satisfy the package‑structure requirement.

## 3. Run the Pipeline
```bash
python -m src.cli.run_pipeline \
    --seed 42 \
    --log-level INFO
```
The script executes the ordered phases described in `plan.md`:

1. **download** – fetches the BFI‑2 CSV from the verified Hugging Face URL, records SHA‑256 checksum, stores under `data/raw/`. If the linked Last.fm listening data is missing, the script aborts with a clear error.  
2. **preprocess** – validates the BFI schema; hashes `user_id`; imputes/excludes missing demographics (FR‑007); if genre data are present, maps raw tags using the lookup table, computes proportion scores (with 1‑minute pseudocount), log‑transforms, and applies ILR transformation; writes `processed_dataset.parquet`.  
3. **correlate** – computes **Pearson** correlation coefficients for each trait–genre pair (if genre data exist).  
4. **adjust** – applies Bonferroni correction (α = 0.001).  
5. **regress** – fits five linear models (one per trait) with ILR components + age + gender_onehot + country_onehot (no total minutes).  
6. **diagnostics** – runs Shapiro‑Wilk, Breusch‑Pagan, VIF; drops predictors with VIF > 5; logs warnings.  
7. **effects** – converts Pearson r → Cohen’s d; bootstraps 10 000 resamples for 95 % CI; augments `correlation_results.csv`.  
8. **visualize** – creates `correlation_heatmap.png` and `regression_coefficients.png`.  
9. **report** – merges all tables into `results_report.csv`, explicitly labeling non‑significant pairs as “Non‑significant (adjusted p ≥ 0.001)”.  
10. **contract** – validates **all** output artifacts against their JSON‑Schema contracts (`dataset.schema.yaml`, `processed_dataset.schema.yaml`, `analysis_output.schema.yaml`, etc.).  
11. **clean‑up & logging** – writes `pipeline.log` with timings, checksum info, rows/predictors dropped.

If any step fails (e.g., checksum mismatch, schema violation, missing linked data), the pipeline aborts with a clear error message and the CI job is marked failed.

## 4. Expected Outputs (when linked data are present)
- `data/processed/processed_dataset.parquet` – analysis‑ready dataframe.  
- `results/correlation_results.csv` – Pearson r, raw & adjusted p‑values, Cohen’s d, 95 % CI.  
- `results/regression_results.csv` – coefficients for each trait model.  
- `results/coefficient_deltas.csv` – baseline vs. full model betas, delta, VIF, validity flag.  
- `results/correlation_heatmap.png` – heatmap of Pearson r values.  
- `results/regression_coefficients.png` – bar plot of regression coefficients.  
- `results/results_report.csv` – consolidated human‑readable report with explicit “Non‑significant (adjusted p ≥ 0.001)” labels.  

## 5. CI Integration
The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs the above command on every push. The workflow asserts that total runtime < 6 h and that all contract validations pass.

---  