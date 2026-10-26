# Quickstart: Predicting Corrosion Rates with Interaction Effects  

This guide reproduces the full analysis (ingestion, preprocessing, feature engineering, model training, significance testing, SHAP interpretation, and reporting) on a CPU‑only GitHub Actions runner (2 vCPUs, ~7 GB RAM, ≤ 6 h wall‑time).

## Prerequisites
- Python 3.11
- Git
- Internet access (only needed to clone the repository; the dataset is version‑controlled)

## Setup
```bash
# Clone the repository
git clone <repo_url>
cd <repo_root>

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install exact‑pin dependencies
pip install -r src/requirements.txt   # matches requirements in code/
# Mirror the file for compliance (the script does this automatically)
cp src/requirements.txt code/requirements.txt
```

## Run the Full Pipeline
```bash
python -m src.run_all
```
`src/run_all.py` orchestrates the phases defined in `plan.md`:

1. **Ingestion** – validates columns, harmonizes units, imputes, one‑hot encodes, standardizes, writes `cleaned_dataset.csv`, `metadata/dataset.yaml`, and `vif_diagnostics.json`.  
2. **Feature Engineering** – creates interaction and polynomial features, writes `features.parquet` and `feature_names.txt`.  
3. **Splitting** – builds stratified GroupKFold splits, saves `splits.pkl`.  
4. **Training** – fits Full and Null Random Forest (and optionally Gradient Boosting) models within `max_depth ≤ 5`, `n_estimators ≤ 200`, persists the best models and `model_artifact.yaml`.  
5. **Baseline** – trains a mean‑only predictor, records its R² and RMSE, and compares it to the Full model to satisfy **SC‑001**.  
6. **Evaluation – Interaction‑Gain** – runs the **interaction‑column permutation test** (shuffle only the engineered interaction columns) to assess whether interaction features add predictive value (Phase 6 in the plan).  
7. **Evaluation – Conditional Permutation‑Importance** – for each interaction column orthogonalizes it against its base features, shuffles the residuals **1 000 times**, computes ΔRMSE, derives upper‑tail empirical p‑values, and applies **Benjamini‑Hochberg** correction.  
8. **Interpretation** – computes SHAP interaction values for the top‑5 interactions, generates PNG figures under `outputs/figures/`.  
9. **Sensitivity** – sweeps `max_depth` ∈ {3,4,5}, records top‑5 feature lists, computes Jaccard similarity (≥ 0.8 required), and optionally runs an exploratory sweep with relaxed limits (`max_depth ≤ 6`, `n_estimators ≤ 250`) for power diagnostics (not used for final claims).  
10. **Reporting** – assembles `report.md` with baseline vs. Full performance, interaction‑gain test outcome, BH‑adjusted interaction importance, SHAP visualisations, hyper‑parameter stability, and an explicit **associational** disclaimer.  
11. **Verification** – runs `pytest src/tests/` to ensure contract compliance; any failure aborts the CI run.

## Test Suite
```bash
pytest src/tests/
```
The suite checks:

- Contract compliance (`contracts/cleaned_dataset.schema.yaml`, `contracts/model_artifact.schema.yaml`).  
- Presence of all expected output files.  
- Successful execution of each pipeline module without errors.

All tests must pass for the CI job to be considered successful.

## Expected Outputs
| Path | Description |
|------|-------------|
| `data/processed/cleaned_dataset.csv` | Validated, imputed, standardized dataset. |
| `data/processed/features.parquet` | Feature matrix with engineered interactions. |
| `data/processed/feature_names.txt` | Plain‑text list of feature names (one per line). |
| `data/processed/splits.pkl` | Serialized GroupKFold split indices. |
| `data/results/best_full_model.joblib` | Serialized Full model. |
| `data/results/best_null_model.joblib` | Serialized Null model. |
| `data/results/model_artifact.yaml` | Model metadata (conforms to schema). |
| `data/results/baseline_performance.json` | Baseline mean‑only model metrics (R², RMSE). |
| `data/results/vif_diagnostics.json` | VIF values for base predictors. |
| `data/results/interaction_gain_test.json` | Interaction‑column permutation test result (ΔRMSE, p‑value). |
| `data/results/interaction_permutation_importance.json` | Raw and BH‑adjusted p‑values for each interaction. |
| `data/results/sensitivity.json` | Hyper‑parameter stability diagnostics (Jaccard scores, VIF with interactions). |
| `outputs/figures/*.png` | SHAP summary, interaction dependence, and PDP plots. |
| `report.md` | Full narrative with metrics, statistical tests, and disclaimer. |
| `metadata/dataset.yaml` | Provenance (DOI/URL, SHA‑256, column list). |

## Runtime & Resource Summary
- **Total wall‑time**: ≤ 6 h (empirically on the free tier).  
- **Peak RAM**: Monitored via `psutil`; if > 7 GB, a stratified sample (seed 42) is used automatically (FR‑003).  

## Important Notes
- All findings are **associational**, not causal (SC‑006).  
- If a required column is missing from the supplied CSV, the pipeline aborts with `Error: MISSING_VARIABLE [column_name] in [dataset_source]` (FR‑001).  
- The permutation test implemented is an **interaction‑column permutation test** (shuffling only interaction features) to isolate the contribution of interactions, satisfying FR‑002 and the reviewer’s correction.  
- Conditional permutation importance uses orthogonalization and an **upper‑tail** p‑value, with 1 000 shuffles and Benjamini‑Hochberg correction, addressing FR‑012 and SC‑004.  

---
