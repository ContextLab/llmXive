# Tasks: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts, and existing code base.  
**Goal**: Deliver a reproducible end‑to‑end pipeline that ingests the OpenNeuro ds003XXX dataset, extracts 30 microstate features per participant, trains an Elastic Net regression model with rigorous statistical validation, and produces a complete diagnostics report. All scientific requirements (FR‑001 – FR‑007, SC‑001 – SC‑005) must be satisfied and verifiable by the CI tests.

---

## Phase 0 – Project scaffolding (must be finished before any scientific work)

- [X] **T001**  Create the required directory hierarchy **and** a helper script `scripts/create_dirs.sh` that runs `mkdir -p data/raw data/processed artifacts state code tests`.  
  **Path(s)**: `data/raw/`, `data/processed/`, `artifacts/`, `state/`, `code/`, `tests/`, `scripts/create_dirs.sh`.  
  **Verification**: `scripts/create_dirs.sh` exits 0 and a CI test (`tests/integration/test_structure.py`) asserts that each of the six directories exists after script execution.

- [X] **T002**  Initialise a Python 3.11 project and add a pinned `requirements.txt` containing `mne`, `scikit-learn`, `numpy`, `pandas`, `scipy`, `statsmodels`, `joblib`, `pyyaml`.  
  **Path**: `requirements.txt`.  
  **Verification**: `pip install -r requirements.txt` succeeds in CI; a unit test checks that the file contains at least the listed packages with version specifiers.

- [X] **T003**  Configure linting (`ruff`) and formatting (`black`) via `pyproject.toml`.  
  **Path**: `pyproject.toml`.  
  **Verification**: `ruff check .` and `black --check .` both return exit‑code 0 in CI.

- [X] **T004**  Implement `code/utils.py` with:  
  * deterministic seed pinning,  
  * a lightweight logger,  
  * `record_artifact_hash(filepath)` and `compute_checksum(filepath)` for Constitution Principles V & III.  
  **Verification**: unit test `tests/unit/test_utils.py` checks that two identical files produce identical SHA‑256 hashes and that the logger writes to `state/log.txt`.

- [X] **T005**  Add `scripts/pre-run-validation.sh` that calls `python -m code.utils --validate-citations`. The script exits non‑zero if any required citation is missing.  
  **Path**: `scripts/pre-run-validation.sh`.  
  **Verification**: CI step runs the script; a failing citation causes the pipeline to abort.

- [ ] **T006**  Implement `code/data_loader.py` with `DataChunk` handling via `numpy.memmap` to respect the ≈ 7 GB RAM limit. The loader streams the OpenNeuro ds003XXX files, creates chunk metadata, and yields chunk objects to downstream code.  
  **Verification**: integration test `tests/integration/test_data_loader.py` asserts that total RAM usage stays below 6 GB while processing the full dataset.

- [X] **T007**  Create `code/config.py` exposing constants such as `EXPECTED_FEATURE_COLUMNS` (the ordered list of the 30 feature names) and default paths (`RAW_DIR`, `PROCESSED_DIR`, `ARTIFACTS_DIR`).  
  **Verification**: a unit test imports the module and checks that `len(EXPECTED_FEATURE_COLUMNS) == 30` and that all names match the schema in `contracts/features.schema.yaml`.

---

## Phase 1 – Data ingestion & preprocessing (User Story 1, P1)

- [ ] **T008**  Implement the full preprocessing pipeline in `code/preprocessing.py`:  
  * Re‑reference to average mastoids,  
  * Band‑pass filter 1–40 Hz,  
  * ICA‑based ocular/muscle artifact removal,  
  * Exclude participants with `< 4 min` of clean data (log a warning),  
  * Microstate segmentation (canonical A‑D maps),  
  * Extraction of the **exact 30 features** (4 mean durations, 4 occurrence rates, 16 transition probabilities, 6 spectral‑power bands).  
  **Verification**: unit test `tests/unit/test_preprocessing.py` confirms that for a synthetic EEG file the output DataFrame has 30 columns, no NaNs, and correct column names; an integration test `tests/integration/test_full_preprocess.py` runs the pipeline on a 5‑participant real subset and checks that `data/processed/feature_matrix.csv` exists.

- [ ] **T009**  Aggregate per‑participant features and heat‑pain thresholds into `data/processed/feature_matrix.csv`. Include a sanity‑check that the CSV header exactly matches `config.EXPECTED_FEATURE_COLUMNS` and that `df.isna().sum().sum() == 0`.  
  **Verification**: CI step runs `python -c "import pandas as pd; df=pd.read_csv('data/processed/feature_matrix.csv'); assert set(df.columns)==set(config.EXPECTED_FEATURE_COLUMNS)"`.

---

## Phase 2 – Model training & validation (User Story 2, P2)

- [ ] **T010**  Implement `code/modeling.py::train_nested_cv` which performs **nested 5‑fold cross‑validation** with Elastic Net (α = 0.5) on the feature matrix, returns per‑fold Pearson r, MAE, and the mean across outer folds.  
  **Verification**: unit test `tests/unit/test_modeling_cv.py` checks that the function returns a dict containing keys `r_mean`, `mae_mean`, and that each value is a float.

- [ ] **T011**  Implement **global permutation testing** (FR‑004) in `code/modeling.py::global_permutation_test`. For each of **1 000 permutations**: shuffle the target labels **once per outer CV iteration**, run the full nested CV, and store the resulting mean r.  
  **Verification**: integration test `tests/integration/test_permutation.py` asserts that the returned null distribution length is 1 000 and that the runtime flag `max_permutations=1000` is respected.

- [ ] **T012**  Implement **bootstrap resampling** (200 iterations) for the observed Pearson r to obtain a 95 % confidence interval, with a runtime‑limit guard that aborts and logs a warning if the estimated total time would exceed the 6‑hour CI budget.  
  **Path**: `code/modeling.py::bootstrap_ci`.  
  **Artifact**: `artifacts/bootstrap_ci.json` containing `{ "ci_lower": ..., "ci_upper": ... }`.  
  **Verification**: unit test `tests/unit/test_bootstrap.py` confirms that the function returns the two‑element tuple and that a mocked timer triggers the guard when the projected runtime > 6 h.

- [ ] **T013**  Compute the **empirical p‑value** by comparing the observed mean r to the permutation null distribution (FR‑004). Store the p‑value together with r, MAE, and the CI in `artifacts/model_result.json`.  
  **Path**: `code/modeling.py::compute_empirical_pvalue`.  
  **Verification**: unit test `tests/unit/test_pvalue.py` creates a synthetic null distribution, calls the function, and asserts `0 ≤ p ≤ 1` and that `p` equals the proportion of null r’s ≥ observed r; also checks that the JSON file contains the `p_value` field.

- [ ] **T014**  Extend `code/main.py` to orchestrate the steps: data loading → preprocessing → feature matrix creation → nested CV training → permutation test → bootstrap CI → p‑value calculation → artifact hashing. Log total pipeline duration and assert it is **< 6 hours** (SC‑005).  
  **Verification**: CI runs the full script on the 5‑participant subset; the final log contains `TOTAL_DURATION=...` and the assertion passes.

---

## Phase 3 – Statistical diagnostics & sensitivity analysis (User Story 3, P3)

- [ ] **T015**  Implement `code/diagnostics.py::permutation_importance` that measures the drop in Pearson r after shuffling each feature column (10 repeats per feature) and returns a score per feature.  
  **Verification**: unit test `tests/unit/test_permutation_importance.py` checks that the function returns a dictionary with 30 keys and that all scores are non‑negative.

- [ ] **T016**  Compute **coefficient‑wise p‑values** for the Elastic  Net model (e.g., via Wald statistics or bootstrapped SE), then apply **Benjamini‑Hochberg FDR correction** to those p‑values. Store both raw and FDR‑adjusted p‑values in `artifacts/diagnostics.csv`.  
  **Verification**: unit test `tests/unit/test_fdr_coefficients.py` verifies that the CSV contains columns `feature_name, coefficient, p_value_raw, p_value_fdr`, that the adjusted p‑values are monotonic, and that at least one feature remains significant when appropriate.

- [ ] **T017**  Compute **Variance Inflation Factors** (VIF) for the full predictor set using `statsmodels.stats.outliers_influence.variance_inflation_factor`. Flag any predictor with `VIF > 10` (FR‑006).  
  **Verification**: unit test `tests/unit/test_vif.py` supplies a synthetic design matrix with a known collinear column and asserts that the flagged list includes that column.

- [ ] **T018**  Perform the **median‑split sensitivity sweep** (thresholds: median ± 0.1 °C, median ± 0.05 °C) and, for each cutoff, compute Cohen’s d for the top‑5 predictive features between “high‑pain” and “low‑pain” groups. Store results in `artifacts/median_sensitivity.csv`.  
  **Verification**: integration test `tests/integration/test_median_sensitivity.py` checks that the CSV has five rows (one per threshold) and that effect‑size columns are numeric.

- [ ] **T019**  Conduct a **regularization‑parameter sweep** for Elastic  Net α from 0.0 to 1.0 in 0.05 steps, recording the outer‑fold R² for each α in `artifacts/alpha_sweep.csv`.  
  **Verification**: unit test `tests/unit/test_alpha_sweep.py` confirms that the CSV contains 21 rows and that R² values are between 0 and 1.

- [ ] **T020**  Generate the **diagnostics report** `artifacts/diagnostics_report.md` containing:  
  * A Markdown table of **FDR‑adjusted coefficient p‑values** (highlighting significant features),  
  * A table (or JSON block) of **VIF values** with a “⚠️” flag for any VIF > 10,  
  * Plots/tables summarising the **median‑split** and **α‑sweep** sensitivity analyses, and  
  * The top predictive feature’s **FDR‑adjusted p‑value** explicitly called out.  
  **Verification**: a CI check parses the Markdown file, confirms the presence of all three sections, verifies that at least one feature is marked significant, that any VIF > 10 is flagged, and that the top feature’s adjusted p‑value is reported.

---

## Phase 4 – Documentation & final deliverables

- [ ] **T021**  Write a concise `README.md` that (i) lists the required Python version, (ii) provides installation instructions (`pip install -r requirements.txt`), (iii) shows a minimal command‑line example to run the full pipeline (`python -m code.main --sample 5`), and (iv) points to the locations of the main artifacts (`feature_matrix.csv`, `model_result.json`, `diagnostics_report.md`).  
  **Verification**: CI step runs `markdownlint` and a custom script that extracts the “Usage” code block and executes it on a tiny synthetic dataset; the command must complete without error.

- [ ] **T022**  Run an **end‑to‑end demonstration** on a 5‑participant real subset (provided in `data/raw/sample/`). The run must produce:  
  * `data/processed/feature_matrix.csv` (30 columns, no NaNs),  
  * `artifacts/model_result.json` (r, CI, p‑value, MAE),  
  * `artifacts/diagnostics_report.md`.  
  **Verification**: a CI job named `demo_end_to_end` executes `python -m code.main --sample 5` and asserts the existence and non‑emptiness of the three files; it also checks that `model_result.json["p_value"] < 0.05` *or* logs a clear “p ≥ 0.05” message (the scientific outcome may be null, but the file must be present).

- [ ] **T023**  Ensure all artifact hashes are recorded via `utils.record_artifact_hash` after each major step (feature matrix, model result, diagnostics report, bootstrap CI).  
  **Verification**: unit test `tests/unit/test_hash_recording.py` reads `state/artifact_hashes.yaml` and confirms entries for `data/processed/feature_matrix.csv`, `artifacts/model_result.json`, `artifacts/diagnostics_report.md`, and `artifacts/bootstrap_ci.json`.

---

### Execution order & dependencies

| Task | Depends on |
|------|------------|
| T001–T007 | – (initial scaffolding) |
| T008–T009 | T001–T007 |
| T010–T014 | T008–T009 |
| T015–T019 | T010–T014 |
| T016 | T015 (needs feature matrix) |
| T020 | T016–T019 |
| T021 | – (can be authored anytime after tasks are defined) |
| T022 | T001–T020 (full pipeline) |
| T023 | T022 (hash recording is part of `code/main.py`) |

All tasks are expressed as canonical checklist items; unchecked boxes indicate work still required.  

---  

*All tasks are expressed as canonical checklist items; unchecked boxes indicate work still required.*  