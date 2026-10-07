# Quickstart: Correlation Between Musical Preference & Personality

This guide shows how to run the full analysis on a fresh GitHub Actions runner (or locally) using only the verified BFI‑2 and Last.fm 1‑K datasets.

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
│   ├── bfi_raw.csv
│   └── lastfm_raw.csv
├── processed/
│   └── processed_dataset.parquet
results/
├── correlation_heatmap.png
├── regression_coefficients.png
├── results_report.csv
├── power_analysis.txt
├── coefficient_deltas.csv
├── logs/
│   └── pipeline.log
```

*Note*: The pipeline creates the above directories and also places empty `__init__.py` files in `src/` and `tests/` to satisfy the package structure requirement.

## 3. Run the Pipeline
```bash
python -m src.cli.run_pipeline \
    --seed 42 \
    --log-level INFO
```
The script executes the following ordered phases (see `plan.md`):

1. **download** – fetches the BFI‑2 CSV and the Last.fm 1‑K Users dataset from the verified URLs, records SHA‑256 checksums, and stores them under `data/raw/`.  
2. **preprocess** – validates raw schemas, maps raw genre tags to the lookup table (10 categories), imputes or drops missing demographics, computes `total_minutes`, calculates `genre_proportions`, log‑transforms, and performs ILR transformation → `genre_ilr`.  
3. **power** – writes `results/power_analysis.txt` with required N, actual N, and a “limited power” note if applicable.  
4. **correlate** – produces `results/correlation_results.csv` (Spearman ρ, raw p, adjusted p, Cohen’s d, bootstrap CI).  
5. **adjust** – Bonferroni correction (α = 0.001).  
6. **regress** – fits five ILR‑based linear models (one per trait) and writes `results/regression_results.csv`.  
7. **diagnostics** – runs Shapiro‑Wilk, Breusch‑Pagan, VIF checks; drops offending predictors, logs warnings.  
8. **effects** – adds Cohen’s d (via rank‑biserial conversion) and bootstrap 95 % CIs.  
9. **deltas** – generates `results/coefficient_deltas.csv` (baseline vs. full model betas, delta, VIF, validity flag) and validates it against `contracts/results.schema.yaml`.  
10. **visualize** – creates `results/correlation_heatmap.png` and `results/regression_coefficients.png`.  
11. **report** – merges all tables into `results_report.csv`, including explicit “Non‑significant (adjusted p ≥ 0.001)” labels.  
12. **contract** – validates **every** output artifact (`processed_dataset.schema.yaml`, `analysis_output.schema.yaml`, `correlation_results.schema.yaml`, `regression_results.schema.yaml`, `report.schema.yaml`, `results.schema.yaml`) using `jsonschema`. Abort on any mismatch.  

If any step fails (e.g., checksum mismatch, schema violation, missing `lastfm_username`), the pipeline aborts with a clear error message and the CI job is marked failed.

## 4. Expected Outputs
- `data/processed/processed_dataset.parquet` – ready‑to‑analyze dataframe.  
- `results/correlation_results.csv` – Spearman ρ, p, adjusted p, Cohen’s d, CI.  
- `results/regression_results.csv` – coefficients for each trait model.  
- `results/coefficient_deltas.csv` – baseline vs. full model betas, delta, VIF, validity flag.  
- `results/correlation_heatmap.png` – visual matrix of ρ values.  
- `results/regression_coefficients.png` – bar plot of regression coefficients.  
- `results/results_report.csv` – consolidated human‑readable report.  
- `results/power_analysis.txt` – required sample size, actual N, and power note.  

## 5. Re‑Running / Troubleshooting
- To **force re‑download** of raw data: delete `data/raw/*` and rerun.  
- To **change the random seed** (affects bootstrap resampling): add `--seed <int>` to the CLI.  
- Logs are stored in `results/logs/pipeline.log`; consult them for any dropped rows or predictors.

## 6. CI Integration
The repository includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs the above command on every push. The workflow asserts that total runtime < 6 h and that all contract validations pass.

--- 