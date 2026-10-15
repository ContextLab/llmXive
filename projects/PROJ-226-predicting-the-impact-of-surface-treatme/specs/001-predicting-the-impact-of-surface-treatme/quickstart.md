# Quickstart: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

This guide walks you through running the full pipeline on a fresh GitHub Actions runner (or locally) from data acquisition to final report generation.

## Prerequisites
- **Python 3.11** (installed automatically in the CI environment).  
- **Internet access** (required for downloading the open dataset).  
- **GitHub Actions free‑tier runner** (2 CPU, ≈ 7 GB RAM) – **no GPU needed**.  

## Setup
```bash
# 1. Clone the repository (already done in CI)
git checkout 001-predicting-adhesion-strength

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## Step‑by‑Step Execution

| Step | Command | Description |
|------|---------|-------------|
| **0** | `python -m llmxive_toolkit.paths.ensure_dirs` | Creates `data/`, `data/raw/`, `data/cleaned/`, `models/`, `results/`, `figures/`, `contracts/` if missing. |
| **1** | `python code/ingest.py` | Attempts to download an **open adhesion dataset that contains all required variables**. If none is found, the script aborts with a clear error (see Phase 0 in `plan.md`). No synthetic data is used for the primary scientific analysis. |
| **2** | `python code/preprocess.py` | Performs unit conversion, canonicalisation, one‑hot encodes `pair_id`, median imputation, and writes `data/cleaned/cleaned.csv`. |
| **3** | `python code/split.py` | Generates `train.csv`, `val.csv`, `test.csv` under `data/cleaned/` using the grouped 70/15/15 split and excludes sparse groups (< 5 records). |
| **4** | `python code/train_models.py` | Runs grid search (≤ 50 combos) for RF, GB, LR; computes **bootstrapped 95 % CI** for validation R²; selects the best model (validation R² lower‑CI ≥ 0.5). Saves model artifacts to `models/`; writes `results/hyperparams.json`. |
| **5** | `python code/evaluate.py` | Computes test metrics, selects best model, writes `results/evaluation.json`. |
| **6** | `python code/permutation_test.py` | Executes a **nested permutation test** (outer 5‑fold CV, inner CV for hyper‑parameter tuning, 1 000 shuffles per outer test fold) and appends `p_value` to `results/evaluation.json`. |
| **7** | `python code/shap_analysis.py` | Generates SHAP values, saves `figures/shap_summary.png` and `results/shap_ranking.json`. |
| **8** | `python code/report.py` | Compiles the final Markdown and JSON report (`results/report.md`, `results/report.json`), includes all four visualisations and bootstrapped CI. |
| **9** | `python -m pytest -vv tests/contract/` | Validates that all output files satisfy the schemas in `contracts/`. |

## Expected Runtime & Resources
- **Total wall‑clock time**: ≈ 3.5 h on the CI runner.  
- **Peak RAM usage**: ≈ 2.5 GB (during model training).  

## Verifying Success
The CI job passes if **all** contract tests succeed **and** the final report contains:

- `final_r2` **lower‑CI ≥ 0.5** **and** `permutation_p_value` < 0.05 (SC‑001 & SC‑002) **or** a clearly labelled “null” result (FR‑012).  
- All four PNG files are present in `figures/`.  
- `results/report.json` validates against `contracts/analysis_result.schema.yaml`.  

If the dataset cannot be fetched (see **Data Availability** in `plan.md`), the pipeline stops at Step 1 with an informative error, prompting the project lead to provide a suitable open dataset or approve a specification revision.  

## Reproducibility
All scripts set `np.random.seed(42)` and pass `random_state=42` to scikit‑learn estimators, guaranteeing deterministic results across runs.  

---
