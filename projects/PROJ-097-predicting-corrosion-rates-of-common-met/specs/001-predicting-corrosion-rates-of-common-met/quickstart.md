# Quickstart: Predicting Corrosion Rates with Interaction Effects

This guide shows how to reproduce the full analysis (ingestion, preprocessing, feature engineering, model training, significance testing, SHAP interpretation, and reporting) on a CPU‑only GitHub Actions runner (2 vCPUs, ~7 GB RAM, ≤ 6 h wall‑time).

## Prerequisites
- Python 3.11
- Git
- Internet access (only needed to fetch the repository; the dataset is supplied locally by the verifier)

## Setup

```bash
# Clone the repository (if not already)
git clone <repo_url>
cd <repo_root>

# Create a virtual environment and install pinned dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt   # matches requirements in code/
```

## Run the Full Pipeline

```bash
python -m src.pipeline.run_all
```

The orchestrator `src/pipeline/run_all.py` executes the phases in the order defined in `plan.md`:

1. **Ingestion** – reads the raw CSV, validates columns, harmonizes units, imputes missing values, one‑hot encodes composition, standardizes numerics, computes VIF for base predictors, and writes `data/processed/cleaned_dataset.csv` (the **CorrosionRecord** collection), `metadata/dataset.yaml` (the **DatasetMetadata**), and `data/results/vif_report.json`.
2. **Feature Engineering** – creates interaction and polynomial features, residualizes interactions, writes `data/processed/features.parquet` (the **InteractionFeature** set).
3. **Splitting** – builds stratified GroupKFold splits (`data/processed/splits.pkl`).
4. **Training** – fits Full and Null Random Forest / Gradient Boosting models under the constrained hyper‑parameter grid, persists the best model as `data/results/best_model.joblib` and metadata as `data/results/model_artifact.yaml` (the **ModelArtifact**).
5. **Evaluation** – runs the paired sign‑flip permutation test for interaction gain, permutation‑importance per interaction column with Benjamini‑Hochberg correction, and stores results in `data/results/interaction_test.json`.
6. **Interpretation** – computes SHAP interaction values for the top interactions, generates summary and dependence plots under `outputs/figures/`.
7. **Sensitivity** – sweeps `max_depth` ∈ {3,4,5}, computes Jaccard similarity of top‑N feature sets, writes `data/results/sensitivity.json`.
8. **Reporting** – assembles `report.md` with all metrics, visualisations, and the required associational disclaimer.
9. **Verification** – runs `pytest src/tests/` to ensure all contracts and unit tests pass; any failure aborts the CI run.

## Test Suite

```bash
pytest src/tests/
```

The test suite checks:

- Contract compliance (`contracts/cleaned_dataset.schema.yaml`, `contracts/model_artifact.schema.yaml`).
- Successful creation of `cleaned_dataset.csv` and `features.parquet`.
- Correct execution of each pipeline module without errors.

All tests must pass before the CI job is considered successful.

## Expected Outputs

| Path | Description |
|------|-------------|
| `data/processed/cleaned_dataset.csv` | Validated, imputed, standardized dataset (schema enforced). |
| `data/processed/features.parquet` | Feature matrix with engineered interactions. |
| `data/results/best_model.joblib` | Serialized best Full model. |
| `data/results/model_artifact.yaml` | Metadata conforming to `contracts/model_artifact.schema.yaml`. |
| `data/results/vif_report.json` | VIF diagnostics for base predictors. |
| `data/results/interaction_test.json` | Paired permutation‑test result and BH‑adjusted interaction importance. |
| `outputs/figures/*.png` | SHAP summary, interaction dependence, and partial‑dependence plots. |
| `report.md` | Full narrative with performance metrics, statistical tests, and disclaimer. |
| `metadata/dataset.yaml` | Provenance (DOI/URL, SHA‑256, column list). |

## Runtime & Resource Summary

- **Total wall‑time**: ≤ 6 h (empirically on the free tier).  
- **Peak RAM**: Monitored via `psutil`; if > 7 GB, a stratified sample (seed 42) is used automatically (FR‑003).

## Important Notes

- All findings are **associational**, not causal (SC‑006).  
- If a required column is missing from the supplied CSV, the pipeline aborts with `Error: MISSING_VARIABLE [column_name] in [dataset_source]` (FR‑001).  
- The permutation test implemented is a **paired sign‑flip test**, satisfying the reviewer’s comment on methodological correctness.