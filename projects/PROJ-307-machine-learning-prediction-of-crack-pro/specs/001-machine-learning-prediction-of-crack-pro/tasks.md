# Tasks: Machine Learning Prediction of Crack Propagation Rates in Metals

**Input**: `spec.md`, `plan.md`, existing research artifacts, and reviewer feedback.  
All tasks follow the canonical `- [ ] T### [P?] [USx?] description with file path` format. Checked boxes (`[X]`) indicate work already verified; unchecked boxes (`[ ]`) are pending. Duplicate IDs have been eliminated and each task is uniquely numbered.

---

## Phase 1 – Project scaffolding (foundational, must be completed before any user‑story work)

- [ ] T001a Create the top‑level directory layout for the feature  
  `projects/001-crack-propagation-ml/` with sub‑folders `code/`, `data/`, `tests/`, `specs/`, `contracts/`.  
  *Verification*: `tree` output shows the expected hierarchy; all folders are present.

- [ ] T001b Add `__init__.py` files and minimal placeholder modules so that every package under `code/` is importable.  
  *Files*: `code/__init__.py`, `code/data/__init__.py`, `code/models/__init__.py`, `code/analysis/__init__.py`, `code/utils/__init__.py`.  
  *Verification*: `python -c "import code"` runs without `ImportError`.

- [ ] T002 Initialise a Python 3.11 project with a pinned `requirements.txt` and a `pyproject.toml` that lists the exact versions of all dependencies required by the plan.  
  *Verification*: `pip install -r requirements.txt` succeeds; `python -m build` reports a valid build.

- [ ] T003 Configure linting (`ruff`) and formatting (`black`) tools and add them to the CI workflow.   <!-- FAILED-IN-EXECUTION: scripts/run_lint.sh exit=2 -->
  *Verification*: `ruff .` and `black --check .` both exit with status 0 in the CI run.

- [ ] T004 Create `code/config.py` containing global random seeds, default hyper‑parameters, and path constants used throughout the pipeline.  
  *Verification*: Importing `code.config` yields the expected attributes (e.g., `SEED`, `DATA_DIR`, `RESULTS_DIR`).

- [ ] T005 Add the **dataset contract** `contracts/dataset.schema.yaml` by copying the authoritative schema from `specs/001-machine-learning-prediction-of-crack-pro/contracts/dataset.schema.yaml` into the project’s `contracts/` directory and validate it with a known good record.  
  *Verification*: `jsonschema.validate(instance, schema)` succeeds for a sample record; the file is present and passes `yamllint`.

- [ ] T006 Add the **output contract** `contracts/output.schema.yaml` by copying the schema from `specs/001-machine-learning-prediction-of-crack-pro/contracts/output.schema.yaml` into `contracts/` and validate a sample `ModelPerformance` JSON.  
  *Verification*: Validation of a sample JSON against the schema returns no errors.

- [ ] T007 Create `code/utils/__init__.py` and a skeleton `code/utils/stats.py` (currently empty but importable).  
  *Verification*: `import code.utils.stats` works; the module is listed in the package.

---

## Phase 2 – Baseline pipeline (User Story 1 – P1)

- [ ] T008 Implement `code/data/loader.py`  
  *Features*: download the NASA Fracture Control Database CSV and the NIST Materials Data Repository CSV, verify SHA‑256 checksums, and validate each row against `contracts/dataset.schema.yaml`.  
  *Path*: `code/data/loader.py` → raw files stored in `data/raw/`.  
  *Verification*: Running `python -m code.data.loader --step download` creates the two CSVs, prints “validation passed”, and exits with status 0.

- [ ] T008a Modify `code/data/loader.py` to import the dataset schema from `contracts/dataset.schema.yaml` and perform per‑record validation using `jsonschema.validate`.  
  *Verification*: Loader logs “record X validated” for each row; failures raise a clear exception.

- [ ] T009 Implement the preprocessing pipeline in `code/data/preprocessor.py`  
  *Steps*:  
  1. Load raw CSVs, filter rows with positive `da_dN` and `delta_K`.  
  2. Compute `log_da_dN` and `log_delta_K`.  
  3. Impute missing `heat_treatment` with the literal string `"Unknown/Not Specified"`.  
  4. One‑hot encode `heat_treatment` and z‑score scale continuous features (including composition wt %).  
  5. Persist the processed table as `data/processed/processed_fcg.parquet`.  
  *Verification*: The parquet file contains the columns `log_da_dN`, `log_delta_K`, `composition`, `heat_treatment_*`; a quick `pandas.read_parquet` shows no NaNs in required columns.

- [ ] T010a Build the baseline model in `code/models/baseline.py` and a driver in `code/main.py` that:  
  1. Loads the processed data.  
  2. Trains a simple linear regression using **only** `log_delta_K` to predict `log_da_dN`.  
  3. Computes the coefficient of determination (`R²`) on a held‑out test split.  
  4. Performs a **permutation test** (10 000 permutations) against a null intercept‑only model and records the observed p‑value.  
  5. Writes a JSON metric file conforming to `contracts/output.schema.yaml` (e.g., `results/baseline_metrics.json`).  
  6. Generates a partial‑dependence plot of `log_delta_K` vs. `log_da_dN` showing the Paris‑Law slope and saves it to `results/baseline_pdp.png`.  
  *Verification*: After `python -m code.main --step baseline`, the JSON file exists, contains `model_type: "Baseline"`, `r2_score` > 0, and a reported `p_value`; the PNG displays a straight line on log‑log axes.

- [ ] T011 Add a pipeline‑wide column‑validation step in `code/main.py` that calls `verify_required_columns(df, required_columns)` (required columns are listed in `dataset.schema.yaml`). The function aborts with a clear error message if any column is missing.  
  *Verification*: Manually delete `log_delta_K` from the DataFrame, rerun the pipeline, and confirm it exits with non‑zero status and prints “Missing required column: log_delta_K”.

- [ ] T011a Add a JSON‑schema validation step that runs **after** the baseline (and later) metric files are written, checking them against `contracts/output.schema.yaml` before any downstream consumer reads them.  
  *Verification*: If the JSON does not conform, the script raises a `SchemaValidationError` and halts.

---

## Phase 3 – Augmented modeling (User Story 2 – P2)

- [ ] T012 Implement a reusable permutation‑test helper in `code/utils/stats.py`  
  *Signature*: `permutation_test(metric_func, X, y, n_perm=5000, random_state=SEED) -> (observed, p_value)`.  
  *Verification*: Unit test confirms that permuting a constant target yields a p‑value ≈ 1.0.

- [ ] T012a Add a pytest unit‑test file `tests/unit/test_permutation_helper.py` that exercises the helper with a constant target and asserts the p‑value condition.  
  *Verification*: `pytest tests/unit/test_permutation_helper.py -q` passes.

- [ ] T013 Implement the augmented‑model module `code/models/augmented.py` that:  
  1. Accepts the full feature set (`log_delta_K`, composition, one‑hot heat‑treatment).  
  2. Provides two classes – `RandomForestRegressor` and `XGBRegressor` – wrapping scikit‑learn and XGBoost respectively.  
  3. Contains **fallback logic**: if composition columns are absent, train using only `log_delta_K` + heat‑treatment; if heat‑treatment columns are absent, train using only `log_delta_K` + composition.  
  *Verification*: Import the module and instantiate both regressors with a dummy DataFrame missing composition; a warning is logged and training proceeds.

- [ ] T014 Implement hyper‑parameter optimisation in `code/models/trainer.py` using Optuna’s TPE sampler: tune `n_estimators`, `max_depth`, and `learning_rate` for both regressors with **5‑fold stratified CV** (stratified by `alloy_family`). Enforce an explicit time budget of **1800 seconds** for the entire optimisation run.  
  *Verification*: Running `python -m code.models.trainer --optimize` finishes within the budget and prints the best hyper‑parameters for each model.

- [ ] T015 Extend `code/main.py` with an **augmented training step** that:  
  1. Loads the processed data.  
  2. Calls the Optuna trainer to obtain the best RF and XGB models.  
  3. Computes `R²` for each model on the held‑out test set.  
  4. Calculates **ΔR² = R²_augmented – R²_baseline**.  
  5. Runs the permutation‑test helper (from T012) to obtain a p‑value for the improvement.  
  6. Aggregates feature‑importance across folds, ranks them, and writes the top‑3 non‑`log_delta_K` features to `results/augmented_feature_importance.json`.  
  7. Stores all metrics in `results/augmented_metrics.json` (conforms to the output contract).  
  *Verification*: After the step completes, both JSON files exist, contain the expected fields, and the p‑value ≤ 0.05.

- [ ] T015a Add a dedicated aggregation task that merges per‑fold feature‑importance arrays into a single averaged importance ranking used by T015.  
  *Verification*: The aggregation script produces `results/augmented_feature_importance.json` with averaged scores.

---

## Phase 4 – Regime identification & sensitivity (User Story 3 – P3)

- [ ] T016 Implement regime detection in `code/analysis/regimes.py` using the **ruptures** library (Kernel Change‑Point Detection). The algorithm automatically splits the test‑set data into three contiguous ΔK regimes (low, mid, high) based on changes in residuals of the baseline model.  
  *Verification*: Running `python -m code.analysis.regimes --detect` prints three interval boundaries that cover the full ΔK range and saves a `results/regime_bounds.json`.

- [ ] T017 For each identified regime, compute:  
  1. **Local R²** for both baseline and augmented models.  
  2. **Dominant features** (top‑3 by importance) within the regime.  
  Store the results in `results/regime_analysis.json` adhering to the `output.schema.yaml` “regime_analysis” section.  
  *Verification*: The JSON contains keys `low`, `mid`, `high` with the required sub‑fields (`local_r2`, `dominant_features`, `stability_score`).

- [ ] T018 Implement a sensitivity analysis in `code/analysis/sensitivity.py` that:  
  1. Perturbs each hyper‑parameter of the augmented models by ±10 % (one at a time).  
  2. Reruns regime detection for each perturbed model.  
  3. Computes a **stability score** defined as the proportion of regime‑ranking orders (Low > Mid > High) that remain unchanged across all perturbations.  
  *Verification*: The script outputs a numeric stability score ≥ 0.9 for the default model and writes it into `results/regime_analysis.json` under each regime.

- [ ] T019 Extend `code/main.py` with a **regime‑analysis step** that orchestrates the three scripts above, generates a regime‑map figure (`results/regime_map.png`), and produces partial‑dependence plots for the top‑3 non‑ΔK features in each regime (`results/pdp_<feature>.png`).  
  *Verification*: After the step, all figures exist, are readable, and CI logs report “Regime analysis completed”.

- [ ] T020 Add a **generalizability check** in `code/main.py` that evaluates the augmented model on a held‑out subset containing alloy families not present in the training split. If such a subset does not exist, the script logs a warning (“No distinct alloy families in test set – generalizability assessment limited”) and continues without error.  
  *Verification*: CI run shows the warning when appropriate and still produces the usual metric files.

---

## Phase 5 – Documentation, performance, and hand‑off

- [ ] T021 Update the project documentation:  
  *Files*: `README.md`, `quickstart.md`.  
  *Content*: installation instructions (including the exact `requirements.txt`), data‑source URLs for NASA and NIST datasets, example CLI commands for each pipeline step, and a brief interpretation of the key results (baseline R², ΔR², regime map).  
  *Verification*: The CI step `make docs` builds the Markdown without errors; the rendered README displays correctly on GitHub.

- [ ] T022 Optimize memory usage (e.g., stream CSVs with `chunksize`, use `parquet` for processed data, delete intermediate DataFrames) **and** add profiling to enforce the **≤ 6 hour** wall‑clock limit and **≤ 7 GB** RSS on the GitHub Actions free‑tier runner.  
  *Verification*: The CI job logs total runtime (“Pipeline completed in Xh Ym”) and peak memory usage (checked via `psutil`); both stay within the specified bounds.

- [ ] T023 Run the complete CI suite, ensuring that **all unit and integration tests pass** and that the final result artifacts (`results/*.json`, `results/*.png`) conform to their respective schemas.  
  *Verification*: GitHub Actions finishes with a green check; `pytest -q` reports “0 failed”.

- [ ] T024 Amend `spec.md` to remove the “nested model F‑test” option from FR‑005, formally ratifying the plan’s decision to use **only permutation tests**.  
  *Verification*: The updated `spec.md` no longer mentions the F‑test; a diff shows the removal and a commit comment references the resolution of the FR‑005 conflict.
