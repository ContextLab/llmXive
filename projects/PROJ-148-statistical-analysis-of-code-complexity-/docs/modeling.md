# Modeling Pipeline Documentation

This document outlines the **model training, evaluation, and reporting pipeline** located in the `code/modeling/` package.
The entry point is `code/modeling/pipeline.py` (`run_training_pipeline`). The pipeline proceeds through the stages below:

1. **`collinearity.py` – `compute_vif`, `drop_high_vif_features`, `main`**
 - Calculates the **Variance Inflation Factor (VIF)** for each metric in the training set to detect multicollinearity.
 - Features with VIF > 5 are removed (or the highest‑VIF feature iteratively until all remaining VIF ≤ 5).
 - Returns a reduced feature list used by downstream models.

2. **`train_primary.py` – `train_primary`**
 - Trains an **L1‑regularized logistic regression** (`LogisticRegression(penalty='l1', solver='saga', max_iter=100)`) on the training data.
 - Enforces the iteration limit (≤ 100) and asserts that at least one coefficient is non‑zero (US2 requirement).
 - Persists the model to `data/model/primary.pkl` via `joblib.dump`.

3. **`train_alternative.py` – `train_alternative`**
 - Trains a **Random Forest classifier** (`n_estimators=200, max_depth=10`).
 - Computes ROC‑AUC on the test split and asserts it is within ±0.05 of the primary model’s ROC‑AUC.
 - Saves the model to `data/model/alternative.pkl`.

4. **`importance.py` – `get_importance`, `save_importance`, `main`**
 - Extracts feature importance:
 - For logistic regression → absolute coefficient values.
 - For Random Forest → `feature_importances_`.
 - Stores a JSON/CSV summary `data/model/feature_importance.csv`.

5. **`compare_models.py` – `compare_models`, `main`**
 - Loads both persisted models and the test set.
 - Computes ROC‑AUC for each and the **Spearman rank correlation** between their feature rankings.
 - Asserts the correlation ≥ 0.7 (US2).
 - Writes a comparison report `data/model/comparison.json`.

6. **`evaluate.py` – `load_test_data`, `load_model`, `compute_metrics`, `plot_calibration`, `evaluate_model`, `main`**
 - Calculates evaluation metrics on the test set: ROC‑AUC, PR‑AUC, Brier score, calibration curve.
 - Generates a calibration plot saved as `figures/calibration.png`.
 - Ensures ROC‑AUC ≥ 0.50 baseline (contract T026).
 - Returns a dictionary of metrics.

7. **`correct_pvalues.py` – `load_pvalues`, `apply_bh_correction`, `compute_fdp`, `save_corrected`, `main`**
 - Loads raw p‑values from feature‑wise statistical tests (if any).
 - Applies **Benjamini–Hochberg** correction via `statsmodels.stats.multitest.multipletests`.
 - Computes the **False Discovery Rate (FDR)** and asserts it ≤ 0.05 (contract T027).
 - Saves corrected p‑values to `data/model/corrected_pvalues.csv`.

8. **`pdp.py` – `ensure_dir`, `generate_partial_dependence_plots`, `main`**
 - Determines the three most important metrics (from step 4).
 - Generates **Partial Dependence Plots** for each using `sklearn.inspection.PartialDependenceDisplay`.
 - Saves PNG files under `figures/pdp_<metric>.png`.

9. **`generate_thresholds.py` – `generate_thresholds`**
 - Uses the primary logistic regression to compute predicted bug‑fix probabilities on the test set.
 - Derives practical thresholds (e.g., probability ≥ 0.5) and writes `data/model/thresholds.csv` with columns `metric, threshold, predicted_probability`.

10. **`report/generate_report.py` – `generate_report`**
 - Compiles all artifacts (performance tables, calibration plot, PDPs, thresholds) into a concise HTML report (`report.html`).
 - Optionally exports a PDF via `weasyprint` if the dependency is installed.

11. **`pipeline.py` – `run_training_pipeline`**
 - High‑level orchestrator that:
 - Loads the preprocessed training and test CSVs (produced by the data pipeline).
 - Executes steps 1‑10 in order, passing data frames between stages.
 - Returns a dictionary containing model objects, evaluation metrics, and paths to generated visualisations.

## Reproducibility & Configuration

- Random seeds are fixed via `utils.config.set_random_seed`.
- All file paths are relative to the project root and stored under `data/` or `figures/`.
- Logging follows the same convention as the data pipeline (`utils.logging.get_logger`).

## Expected outputs

| File / Artifact | Description |
|-----------------|-------------|
| `data/model/primary.pkl` | Logistic regression model |
| `data/model/alternative.pkl` | Random Forest model |
| `data/model/feature_importance.csv` | Coefficient / importance table |
| `data/model/comparison.json` | ROC‑AUC and Spearman correlation summary |
| `figures/calibration.png` | Calibration curve |
| `data/model/corrected_pvalues.csv` | BH‑corrected p‑values |
| `figures/pdp_*.png` | Partial dependence plots for top‑3 metrics |
| `data/model/thresholds.csv` | Practical probability thresholds |
| `report.html` (or `report.pdf`) | Consolidated research report |

## Execution

The full modeling workflow can be launched from the command line:
```bash\npython -m code.modeling.pipeline\n```

This will invoke the entire chain, producing the artifacts listed above and logging progress to `logs/modeling.log`.