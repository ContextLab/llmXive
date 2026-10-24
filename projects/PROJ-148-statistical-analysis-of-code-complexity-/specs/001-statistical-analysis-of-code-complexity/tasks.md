# Tasks: Statistical Analysis of Code Complexity Metrics and Bug Prediction

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, all contract schemas, the original research idea, and any reviewer feedback.

The goal is to deliver a fully reproducible end‑to‑end pipeline that satisfies every functional requirement (FR‑001 … FR‑009) and success criterion (SC‑001 … SC‑003) in the specification.  
Tasks are grouped by research phase; each task is a single unchecked checkbox that can be marked when its artifact exists and its verification step passes.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run a minimal, real‑data pipeline that produces a valid `bug_complexity_dataset.csv` (including a `split` column) and demonstrates that the modeling code works on a realistic subset. |
|------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

- [X] T001 [US1] **Align the data‑model design document** (`specs/001-statistical-analysis-of-code-complexity/data-model.md`) with Section 4 of `spec.md`.  
  - Ensure the column list exactly matches the specification (function‑level keys, integer `cyclomatic_complexity`, `loc`, `token_count`, `nesting_depth`, `halstead_volume`, `bug_label`, `project_id`, `file_path`, `function_name`, `start_line`, `end_line`).  
  - Remove every placeholder marker (`{{claim:…}}`, `[UNRESOLVED‑CLAIM: …]`).  
  - **Verification**: The file contains no placeholder text and its table of fields matches the spec line‑for‑line.

- [ ] T002 [US1] **Implement real data acquisition** in `code/data/download_gh.py`:   <!-- FAILED-IN-EXECUTION: code/data/download_gh.py exit=1 -->
  - Download the **GHTorrent Java dataset** (verified AWS mirror URL) as a compressed archive.  
  - Verify the SHA‑256 checksum recorded in `data/raw/ghtorrent_checksum.txt`.  
  - Extract Java source files (`*.java`) from the archive into `data/raw/<project_id>/`.  
  - Abort with an exception if download or checksum verification fails (no synthetic fallback).  
  - **Verification**: `data/raw/` contains ≥ 10 distinct Java project directories; `ghtorrent_checksum.txt` matches the downloaded archive.

- [ ] T003 [US1] **Implement function‑level bug‑fix labeling** in `code/data/label_bug_fixes.py`:  
  - For each repository, parse `git log --name-only` and regex‑match bug‑fix commit messages (`fix(es|ed)?|bug|close(s|d)? #\d+|resolve(s|d)? #\d+`).  
  - Map changed lines to functions (using start/end line numbers from the extracted metrics) and emit rows with `function_id`, `project_id`, `file_path`, `function_name`, `start_line`, `end_line`, `bug_label=1`.  
  - Emit `bug_label=0` rows for a random sample of untouched functions (fixed random seed).  
  - Fail loudly if a repository yields zero bug‑fix commits.  
  - **Verification**: For every project, `data/interim/labels_<project>.csv` exists with columns including `function_id` and contains at least one row where `bug_label=1`.

- [ ] T004 [US1] **Implement bug‑label validation** (`code/data/validate_bug_labels.py`) and tests:  
  - Provide a function `validate_bug_labels(df: pd.DataFrame, precision_threshold: float = 0.85) -> dict` where `df` has columns `project_id`, `function_id`, `bug_label`.  
  - The function samples a fixed‑seed 100 rows, checks that the regex‑matched keywords are present in the original commit messages, verifies the referenced issue via the GitHub API is labeled “bug” and closed, computes precision, and returns a dict `{ "passed": bool, "precision": float, "sample_size": int }`.  
  - Add/adjust `code/tests/test_bug_label_validation.py` to call the function with the new signature and assert that the `passed` key exists and is a boolean.  
  - **Verification**: `pytest code/tests/test_bug_label_validation.py` passes; a JSON summary `data/results/label_validation.json` is written by the script.

- [ ] T005 [US1] **Update the dataset contract schema** (`specs/001-statistical-analysis-of-code-complexity/contracts/dataset.schema.yaml`) to match Section 4 of the spec exactly:  
  - Include the fields `function_id`, `project_id`, `file_path`, `function_name`, `start_line`, `end_line`, `cyclomatic_complexity` (integer), `loc`, `token_count`, `nesting_depth`, `halstead_volume`, `bug_label` (0/1), `split` (`train`/`test`).  
  - Remove all placeholder markers and any file‑level only columns.  
  - Add a corresponding contract test `code/tests/test_dataset_schema.py` that validates `data/processed/bug_complexity_dataset.csv` against this schema.  
  - **Verification**: The schema file validates against the JSON‑Schema meta‑schema; the test suite passes when run on the generated CSV.

- [ ] T006 [US1] **Extract complexity metrics with Lizard** and produce a function‑level CSV (`data/processed/raw_metrics.csv`).  
  - Run `lizard` on the extracted Java files, emitting one row per function with the required columns (excluding `bug_label` and `split`).  
  - Skip unparsable files with a logged warning; process repositories sequentially to stay within ~7 GB RAM.  
  - **Verification**: The CSV contains ≥ 10 000 rows, all required metric columns, and passes a basic schema sanity check.

- [ ] T007 [US1] **Preprocess the metric data** (impute, log‑transform, handle outliers):  
  - Join `raw_metrics.csv` with function‑level bug labels from T003 to create an interim dataset.  
  - Impute missing values when < 5 % of rows are affected (else drop the rows).  
  - Apply log‑transformation to any metric whose skewness > 2.  
  - Remove rows with > 5 % missing features.  
  - **Verification**: The preprocessed interim CSV (`data/processed/preprocessed.csv`) contains no missing values and all required columns. *Note: Dataset splitting is performed later in T015 after VIF filtering.*

- [ ] T008 [US2] **Compute Variance‑Inflation‑Factor (VIF) diagnostics** and drop high‑VIF predictors:  
  - Implement `code/modeling/vif_report.py` to calculate VIF for all numeric predictors on the preprocessed interim dataset, drop any with VIF > 10, and write `data/results/vif_report.csv`.  
  - **Verification**: The CSV lists VIF values for every retained feature; no retained feature exceeds 10.

- [ ] T009 [US2] **Create the model‑output contract schema** (`specs/001-statistical-analysis-of-code-complexity/contracts/model_output.schema.yaml`) exactly as described in the specification (fields `model_type`, `roc_auc`, `pr_auc`, `calibration_error`, `feature_importance` array with `feature_name`, `importance_score`, `p_value`, `is_significant`, `stability_correlation`, `partial_dependence` array).  
  - Add `code/tests/test_model_output_schema.py` that validates any JSON result file against this schema.  
  - **Verification**: The schema loads without error; the test passes against a real result JSON produced later.

- [ ] T010 [US2] **Train the primary L1‑regularized logistic regression** model:  
  - Use `sklearn.linear_model.LogisticRegression` with `penalty='l1'`, `solver='saga'`, `max_iter=100`, and the global seed from `code/utils/config.py`.  
  - Train on rows where `split='train'` in the unified dataset (`data/processed/bug_complexity_dataset.csv`).  
  - Assert convergence and that the coefficient vector contains at least one non‑zero entry.  
  - Persist the fitted model to `data/model/primary.pkl`.  
  - **Verification**: Loading the pickle yields a model with `coef_` containing non‑zero values and `n_iter_` ≤ 100.

- [ ] T011 [US2] **Train the alternative Random Forest** model:  
  - Use `sklearn.ensemble.RandomForestClassifier` with `n_estimators=100`, `max_depth=10`, and the global seed.  
  - Train on the same training split.  
  - Persist to `data/model/alternative.pkl`.  
  - **Verification**: Model loads; attribute `feature_importances_` is present.

- [ ] T012 [US2] **Fit a statsmodels logistic regression for inference**:  
  - Use `statsmodels.api.Logit` on the training split of the unified dataset to obtain Wald p‑values and coefficient estimates.  
  - Save the fitted model object to `data/model/statsmodels_logit.pkl` and export raw p‑values to `data/results/raw_pvalues.csv`.  
  - **Verification**: The pickle loads; `raw_pvalues.csv` contains a row for each retained predictor.

- [ ] T013 [US2] **Apply Benjamini–Hochberg correction** to logistic‑regression p‑values:  
  - Read `data/results/raw_pvalues.csv`, perform FDR correction, write `data/model/corrected_pvalues.csv` with columns `feature_name`, `raw_p`, `adj_p`, `is_significant`.  
  - Assert that the overall false‑discovery rate ≤ 0.05.  
  - Write a summary JSON `data/results/fdr_report.json` reporting the achieved FDR.  
  - **Verification**: The CSV exists, contains one row per retained feature, and the JSON shows FDR ≤ 0.05.

- [ ] T014 [US2] **Evaluate both models and generate comparison artifacts**:  
  - Compute ROC‑AUC, PR‑AUC, Brier score (calibration error), and a reliability diagram saved as `figures/calibration_plot.png`.  
  - Compute Spearman rank correlation of feature‑importance rankings between the two models.  
  - Assert ROC‑AUC ≥ 0.50 for each model and that the absolute difference between the L1 and RF AUCs is ≤ 0.05 (H2). Also assert rank correlation ≥ 0.70 (SC‑003).  
  - Write a JSON results file `data/results/model_comparison.json` that conforms to the schema from T009 and includes the path to the calibration plot.  
  - **Verification**: The JSON passes the schema test; `figures/calibration_plot.png` exists and is > 10 KB.

- [ ] T015 [US2] **Generate the unified processed dataset with split column**:  
  - Combine the preprocessed, VIF‑filtered data and assign a `split` column (`train`/`test`) using a project‑level stratified 70 % train / 30 % test split.  
  - Write the final CSV to `data/processed/bug_complexity_dataset.csv`.  
  - **Verification**: The file contains the required `split` column, adheres to the updated dataset schema, and the split respects project‑level stratification.

- [ ] T016 [US2] **Generate partial dependence plots and practical thresholds** (addresses RQ3):  
  - For the three most important metrics (by absolute coefficient magnitude in the L1 model), compute PDPs and save a combined figure `figures/pdp_top3.png`.  
  - Determine the metric value at which the predicted bug probability crosses 0.5; write `data/model/thresholds.csv` with columns `metric_name`, `threshold`, `justification`.  
  - **Verification**: PNG > 10 KB; CSV contains exactly three rows with numeric thresholds that lie within the observed range of each metric.

- [ ] T017 [US3] **Write the methods & results report** (`reports/final_report.md`).  
  - Every numeric claim (e.g., ROC‑AUC values, significant p‑values, thresholds) must be cited to a specific line in an artifact (`data/results/...` or `data/model/...`).  
  - Include sections for RQ1 (significance after BH correction), RQ2 (model comparison), RQ3 (thresholds), and a transparent limitations discussion (label noise, project‑level split, pre‑fix snapshot).  
  - **Verification**: A script `code/utils/link_check.py` confirms that every number in the markdown has a source reference; the script exits with status 0.

- [ ] T018 [US3] **Pin exact dependency versions** in `code/requirements.txt`.  
  - Include `lizard==1.17.10`, `pandas==2.2.*`, `scikit-learn==1.4.*`, `statsmodels==0.14.*`, `matplotlib==3.8.*`, `seaborn==0.13.*`, **and** `pymer4==0.2.*`.  
  - **Verification**: `pip install -r code/requirements.txt` completes without version conflicts on the CI runner.

- [ ] T019 [US3] **Validate pymer4 installation** (`code/tests/test_pymer4_import.py`):  
  - Simple test that imports `pymer4` and runs a trivial mixed‑effects model on synthetic data, asserting no exceptions.  
  - **Verification**: The test passes under the pinned `pymer4` version.

- [ ] T020 [US1] **Update `quickstart.md` and execute a full end‑to‑end run**.  
  - Document the exact commands to (1) download data, (2) extract metrics, (3) preprocess, (4) train, (5) evaluate, and (6) generate the report.  
  - Run the documented workflow from a clean checkout; all `pytest` suites must pass, and the final PDF (produced downstream) is reachable via `reports/final_report.pdf`.  
  - **Verification**: The quickstart script exits without error; `pytest -q` reports 0 failures; a CI‑log snippet is saved to `data/results/quickstart_success.log`.

- [ ] T021 [US1] **Implement a manual‑review fallback** for low label precision.  
  - If `validate_bug_labels` (T004) reports `passed=False`, run `code/data/manual_label_review.py` which samples 50 low‑confidence bug‑label rows, writes a markdown review report `data/results/manual_review_report.md`, and aborts the pipeline with exit code 1 and a clear “review required” message.  
  - **Verification**: When precision < 0.85 the pipeline stops, the report file exists, and the exit code is 1.

- [ ] T022 [US1] **Harmonize path layout** across all documentation and code.  
  - Ensure every script, test, and markdown file uses the canonical directories: `data/raw/`, `data/interim/`, `data/processed/`, `data/splits/`, `data/model/`, `data/results/`, `figures/`, `reports/`.  
  - Update stale references in README, quickstart, and any notebooks.  
  - **Verification**: A repository‑wide search finds no path that does **not** start with one of the canonical prefixes.

- [ ] T023 [US2] **Remove the mixed‑effects modeling requirement** (`pymer4`) from the analytical pipeline (retain the dependency for compliance).  
  - Delete any import or usage of `pymer4` from modeling code; the dependency remains listed only to satisfy the spec’s declared packages.  
  - **Verification**: No Python file imports `pymer4`; `pip install -r requirements.txt` succeeds with `pymer4` present but unused.

- [ ] T024 [US2] **Ensure all contract tests are present and pass**.  
  - Run `pytest code/tests/` and confirm that tests for dataset schema (T005), model‑output schema (T009), bug‑label validation (T004), and pymer4 import (T019) succeed.  
  - **Verification**: CI log records “X passed” with zero failures.

---

## Phase 2 – Complete study, validation, and handoff  

| Goal | Produce all deliverables, verify them, and hand the reproducible workflow to the paper pipeline. |
|------|---------------------------------------------------------------------------------------------------|

- [ ] T025 [US3] **Record checksums** for every final artifact (CSV, PKL, PNG, PDF) in `state/artifact_checksums.csv`.  
  - Columns: `artifact_path, sha256`.  
  - **Verification**: A verification script recomputes hashes and reports no mismatches.

- [ ] T026 [US3] **Archive the exact Git commit hash** of the repository used for the final run in `state/run_commit.txt`.  
  - **Verification**: The file contains a 40‑character SHA‑1 string matching `git rev-parse HEAD`.

- [ ] T027 [US3] **Submit the research handoff package** to the downstream paper pipeline (simulated by copying `reports/`, `figures/`, `data/model/`, and `data/results/` into `paper/handshake/`).  
  - Create a sentinel file `paper/handshake/READY`.  
  - **Verification**: The `paper/handshake/` directory contains all expected files and the sentinel file.

--- 

*All tasks above are unchecked; each must be completed and verified before the project can advance to the next stage.* 