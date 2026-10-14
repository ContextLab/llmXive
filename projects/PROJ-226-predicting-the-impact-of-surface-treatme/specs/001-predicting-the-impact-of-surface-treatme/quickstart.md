# Quickstart: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

This guide walks you through running the full pipeline on a fresh GitHub Actions runner (or locally) from data acquisition to final report generation.

## Prerequisites
- **Python 3.11** (installed via the CI environment automatically).  
- **Internet access** (required for downloading the open dataset).  
- **GitHub Actions free‑tier runner** (2 CPU, 7 GB RAM) – no GPU needed.  

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
| **1** | `python code/ingest.py` | **Attempts** to download an open adhesion dataset that contains all required variables. If no such dataset is found, the script aborts with a clear error message directing the user to provide a suitable dataset or revise the specification (see `plan.md`). No synthetic data will be used for the primary scientific analysis. |
| **2** | `python code/preprocess.py` | Performs unit conversion, canonicalization, one‑hot encodes **including `pair_id`**, median imputation, and writes `data/cleaned/cleaned.csv`. |
| **3** | `python code/split.py` | Generates `train.csv`, `val.csv`, `test.csv` under `data/cleaned/` using the grouped split (70/15/15) and excludes sparse groups (< 5). |
| **4** | `python code/train_models.py` | Runs grid search (≤ 50 combos) for RF, GB, LR; computes **bootstrapped 95 % CI** for validation R²; selects the model whose lower CI ≥ 0.5. Saves model artifacts to `models/`; writes `results/hyperparams.json`. |
| **5** | `python code/evaluate.py` | Computes test metrics, selects best model, writes `results/evaluation.json`. |
| **6** | `python code/permutation_test.py` | Executes a **nested permutation test** (outer 5‑fold CV, inner CV for hyper‑parameter tuning, 1 000 shuffles per outer test fold) and appends `p_value` to `results/evaluation.json`. |
| **7** | `python code/shap_analysis.py` | Generates SHAP values, saves `figures/shap_summary.png` and `results/shap_ranking.json`. |
| **8** | `python code/report.py` | Compiles the final Markdown and JSON report (`results/report.md`, `results/report.json`), includes all four visualizations and bootstrapped CI. |
| **9** | `python -m pytest -vv tests/contract/` | Validates that all output files satisfy the schemas in `contracts/`. |

## Expected Runtime & Resources
- Total wall‑clock time **≈ 3.5 h** on the CI runner.  
- Peak RAM usage **≈ 2.5 GB** (during model training).  

## Verifying Success
- The CI job passes if all contract tests succeed and the final report contains:
  - `final_r2` **lower‑CI ≥ 0.5** **and** `permutation_p_value` < 0.05 (SC‑001 & SC‑002) **or** a clearly labeled “null” result (FR‑012).  
  - All four PNG files are present in `figures/`.  
  - `results/report.json` validates against `contracts/analysis_result.schema.yaml`.  

If the dataset cannot be fetched (see **Data Availability** section in `plan.md`), the pipeline will stop at Step 1 with an informative error message, prompting the project lead to provide a suitable open dataset or approve a specification revision.  

## Reproducibility
All scripts set `np.random.seed(42)` and pass `random_state=42` to scikit‑learn estimators to ensure deterministic results across runs.  

## projects/PROJ-226-predicting-the-impact-of-surface-treatme/specs/001-predicting-the-impact-of-surface-treatme/contracts/analysis_result.schema.yaml===
$schema: "http://json-schema.org/draft-07/schema#"
title: "AnalysisResult"
type: object
required:
  - best_model_type
  - final_r2
  - r2_ci_95
  - final_rmse
  - final_mae
  - permutation_p_value
  - top_predictors
  - per_predictor_significance
  - visualizations
  - run_timestamp
  - checksum_report
properties:
  best_model_type:
    type: string
    description: "Model type selected as best (e.g., 'RandomForest')."
  final_r2:
    type: number
    description: "Test‑set R² of the best model."
  r2_ci_95:
    type: array
    minItems: 2
    maxItems: 2
    items:
      type: number
    description: "95 % bootstrapped confidence interval for R²."
  final_rmse:
    type: number
    description: "Test‑set RMSE of the best model."
  final_mae:
    type: number
    description: "Test‑set MAE of the best model."
  permutation_p_value:
    type: number
    description: "Empirical p‑value from 1 000‑shuffle permutation test."
  top_predictors:
    type: array
    items:
      type: string
    description: "Ordered list of top‑3 features by mean absolute SHAP value."
  per_predictor_significance:
    type: object
    additionalProperties:
      type: number
    description: "Mapping from feature name to p‑value (linear model coefficients)."
  visualizations:
    type: object
    required:
      - predicted_vs_actual
      - residual_histogram
      - shap_summary
      - parameter_response_curves
    properties:
      predicted_vs_actual:
        type: string
        description: "Relative path to PNG of predicted vs. actual scatter plot."
      residual_histogram:
        type: string
        description: "Relative path to PNG of residual histogram."
      shap_summary:
        type: string
        description: "Relative path to PNG of SHAP summary plot."
      parameter_response_curves:
        type: string
        description: "Relative path to PNG of parameter‑response curves."
  run_timestamp:
    type: string
    format: date-time
    description: "ISO‑8601 timestamp of the analysis run."
  checksum_report:
    type: object
    description: "SHA‑256 checksums for all output artifacts."
    additionalProperties:
      type: string
      description: "Hexadecimal SHA‑256 checksum."