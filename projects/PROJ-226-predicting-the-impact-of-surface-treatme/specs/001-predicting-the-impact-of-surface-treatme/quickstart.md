# Quickstart: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

This guide walks you through running the full pipeline on a fresh GitHub Actions runner (or locally) from data acquisition to final report generation.

## Prerequisites
- **Python 3.11** (installed automatically in the CI environment).  
- **Internet access** (required only for installing packages).  
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
| **1** | `python code/download_data.py` | Attempts to download the **verified open dataset** that contains all required variables. If no such dataset is available, the script aborts with a clear error message indicating the data‑source limitation. |
| **2** | `python code/validate_units.py` | Generates `data/raw/adhesion_units.json` (unit‑metadata) from source metadata files and verifies unit consistency; raises `UnitMismatchError` on mismatch. |
| **3** | `python code/preprocess.py` | Performs unit conversion, canonicalisation of `treatment_type`, median imputation per substrate class, adds missing‑indicator columns, and writes `data/cleaned/cleaned.csv`. |
| **4** | `python code/split.py` | Generates `train.csv`, `val.csv`, `test.csv` under `data/cleaned/` using a grouped 70/15/15 split and excludes sparse groups (< 5 records). |
| **5** | `python code/train_models.py` | Runs grid search (≤ 50 combos) for RF, GB, LR; computes block‑bootstrap 95 % CI for validation R²; saves model artifacts to `models/`; writes `results/hyperparams.json`. |
| **6** | `python code/evaluate.py` | Computes test metrics, applies the **threshold justification** (validation R² lower‑CI ≥ 0.5 & permutation p < 0.05). If criteria are unmet, a “null” result is recorded per FR‑012. Writes `results/evaluation.json`. |
| **7** | `python code/permutation_test.py` | **Conditional**: runs the permutation test (1 000 shuffles) on the test set **only if a real dataset was successfully downloaded**; appends `p_value` to `results/evaluation.json`. |
| **8** | `python code/confounder_model.py` | (Optional) Fits a mixed‑effects model with `pair_id` random intercept, writes `results/mixed_effects.json`, and logs performance differences. |
| **9** | `python code/shap_analysis.py` | Generates SHAP values, saves `figures/shap_summary.png` and `results/shap_ranking.json`. |
| **10** | `python code/report.py` | Compiles the final Markdown and JSON report (`results/report.md`, `results/report.json`), includes all four visualisations and the mixed‑effects summary (if run). The report explicitly states whether the results are **illustrative** (synthetic fallback) or **empirical** (real data). |
| **11** | `python -m pytest -vv tests/contract/` | Validates that all output files satisfy the schemas in `contracts/`. |

## Expected Runtime & Resources
- **Total wall‑clock time**: ≤ 4 h on the CI runner (if a real dataset is present).  
- **Peak RAM usage**: ≤ 2 GB (during model training).  

## Power‑Analysis Guardrail
Before Step 3, the pipeline checks that the cleaned dataset contains **≥ 200 usable records** (the a‑priori power analysis target). If the dataset falls short, the pipeline aborts with a clear error message.

## Verifying Success
The CI job passes if **all** contract tests succeed **and** the final report contains:

- `final_r2` with **lower‑CI ≥ 0.5** **and** `permutation_p_value` < 0.05 **or** a clearly labelled “null” result (FR‑012).  
- All four PNG files are present in `figures/`.  
- `results/report.json` validates against `contracts/analysis_result.schema.yaml`.  

If no verified dataset is available, the pipeline will still run the synthetic fallback (steps 2‑10) but the final report will be labeled **illustrative** and will **not claim** achievement of SC‑001 or SC‑002.

## Reproducibility
All scripts set `np.random.seed(42)` and pass `random_state=42` to scikit‑learn estimators, guaranteeing deterministic results across runs.  

---

