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
| **1** | `python code/download_data.py` | Downloads the **Open Materials Adhesion** dataset from Hugging Face, verifies SHA‑256 checksums, and writes raw files to `data/raw/`. Also **checks that all required columns are present**; aborts with a clear error if any are missing. |
| **2** | `python code/preprocess.py` | Performs unit conversion, canonicalisation, one‑hot encoding of `pair_id`, **median imputation plus missingness indicators**, and runs **missing‑data sensitivity analyses** (median vs complete‑case vs iterative). Outputs `data/cleaned/cleaned.csv`. |
| **3** | `python code/split.py` | Generates `train.csv`, `val.csv`, `test.csv` under `data/cleaned/` using a grouped 70/15/15 split and excludes sparse groups (< 5 records). |
| **4** | `python code/train_models.py` | Runs grid search (≤ 50 combos) for RF, GB, LR; computes **block‑bootstrap 95 % CI** for validation R² (resampling whole `pair_id` groups); saves model artifacts to `models/`; writes `results/hyperparams.json`. |
| **5** | `python code/evaluate.py` | Computes test metrics, applies **threshold justification** (validation R² lower‑CI ≥ 0.5 & p < 0.05), and writes `results/evaluation.json`. |
| **6** | `python code/permutation_test.py` | Executes the **nested permutation test** (outer 5‑fold CV, 1 000 shuffles per outer fold) and appends `p_value` to `results/evaluation.json`. |
| **6b** | `python code/confounder_model.py` | (a) Adds any extra columns as covariates; (b) fits a mixed‑effects model with `pair_id` as a random intercept using `statsmodels`; (c) writes `results/mixed_effects.json` and compares to primary models. |
| **7** | `python code/shap_analysis.py` | Generates SHAP values, saves `figures/shap_summary.png` and `results/shap_ranking.json`. |
| **8** | `python code/report.py` | Compiles the final Markdown and JSON report (`results/report.md`, `results/report.json`), includes all four visualisations and the mixed‑effects summary. |
| **9** | `python -m pytest -vv tests/contract/` | Validates that all output files satisfy the schemas in `contracts/`. |

## Expected Runtime & Resources
- **Total wall‑clock time**: on the order of a few hours on the CI runner.  
- **Peak RAM usage**: on the order of a few GB (during model training).  

## Power‑Analysis Guardrail
Before proceeding past Step 2, the pipeline checks that the cleaned dataset contains **≥ 200 usable records** (the a priori power analysis target). If this threshold is not met, the script aborts with a clear error message, prompting the project lead to supply more data or revise FR‑001. No synthetic data are used for the primary scientific claim.

## Verifying Success
The CI job passes if **all** contract tests succeed **and** the final report contains:

- `final_r2` with **lower‑CI ≥ 0.5** **and** `permutation_p_value` < 0.05 (SC‑001 & SC‑002) **or** a clearly labelled “null” result (FR‑012).  
- All four PNG files are present in `figures/`.  
- `results/report.json` validates against `contracts/analysis_result.schema.yaml`.  

If the dataset after cleaning yields **fewer than 200 usable records**, the pipeline aborts with an informative error, prompting the project lead to provide additional data or adjust FR‑001. No synthetic data are used for the primary scientific claim.

## Reproducibility
All scripts set `np.random.seed(42)` and pass `random_state=42` to scikit‑learn estimators, guaranteeing deterministic results across runs.  


