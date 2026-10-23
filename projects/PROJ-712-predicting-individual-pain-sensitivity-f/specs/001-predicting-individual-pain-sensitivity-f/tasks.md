# Tasks: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts, and the existing code base.  
**Goal**: Deliver a reproducible end‑to‑end pipeline that (1) ingests the OpenNeuro **ds003542** dataset, (2) extracts the 30 microstate‑derived features per participant, (3) trains an Elastic‑Net regression model with nested 5‑fold cross‑validation, (4) performs the required statistical validation (permutation test, bootstrap CI, FDR, VIF, sensitivity sweeps), and (5) produces the final diagnostics report and documentation. All functional requirements **FR‑001 – FR‑007** and success criteria **SC‑001 – SC‑005** must be satisfied and verifiable by the CI tests.

---

## Phase 0 – Project scaffolding (must be complete before any scientific work)

- [ ] T001 [P0] Create the required project‑owned directory hierarchy via `scripts/create_dirs.sh`; then **run** the integration test `tests/integration/test_structure.py` and capture its JUnit log as `artifacts/test_structure.xml`.  
  **Paths**: `scripts/create_dirs.sh`, `data/raw/`, `data/processed/`, `artifacts/`, `code/`, `tests/`, `artifacts/test_structure.xml`.  
  **Verification**:  
  * Script exits with code 0 and creates the six directories.  
  * `pytest -q tests/integration/test_structure.py --junitxml=artifacts/test_structure.xml` succeeds (exit 0) and the XML contains passing results for all assertions.

- [ ] T002 [P0] Initialise a Python 3.11 project and add a pinned `requirements.txt` containing at least `mne>=1.6`, `scikit-learn>=1.4`, `numpy>=1.26`, `pandas>=2.2`, `scipy>=1.12`, `statsmodels>=0.14`, `joblib>=1.4`, `pyyaml>=6.0`, `datasets>=2.16`, `pytest>=8.0`.  
  **Path**: `requirements.txt`.  
  **Verification**: CI runs `pip install -r requirements.txt`; a unit test `tests/unit/test_requirements.py` checks that each package appears with a version specifier and that the install command returns exit 0.

- [ ] T003 [P0] Configure linting (`ruff`) and formatting (`black`) via `pyproject.toml`.  
  **Path**: `pyproject.toml`.  
  **Verification**: CI runs `ruff check .` and `black --check .`; both must return exit 0. `tests/unit/test_lint.py` asserts that the commands succeeded.

- [ ] T004 [P0] Implement `code/utils.py` with deterministic seed pinning (`np.random.seed(42)`, `random.seed(42)`), a lightweight logger that writes timestamped entries to `artifacts/log.txt`, and a helper `record_artifact_hash(filepath)` that returns the SHA‑256 hash of the file.  
  **Path**: `code/utils.py`.  
  **Verification**: `tests/unit/test_utils.py` checks that two identical files yield identical hashes, that the logger creates `artifacts/log.txt` with a timestamp, and that the seed‑pinning function returns the expected values.

- [ ] T005 [P0] Add `scripts/pre-run-validation.sh` that executes `python -m code.utils --validate-citations`. The script must exit non‑zero if any required citation is missing.  
  **Path**: `scripts/pre-run-validation.sh`.  
  **Verification**: CI runs the script; a failing citation aborts the pipeline (exit ≠ 0). `tests/unit/test_citation_guard.py` asserts the correct exit code for both passing and failing cases.

- [ ] T006 [P0] Implement `code/data_loader.py` with a `DataChunk` class that streams OpenNeuro **ds003542** EEG files via `mne.io.read_raw_*` with `preload=False` (or `numpy.memmap`). The loader must yield chunk objects so that peak RAM stays ≤ 6 GB.  
  **Path**: `code/data_loader.py`.  
  **Verification**: `tests/integration/test_data_loader.py` asserts that processing the full dataset never exceeds 6 GB of resident memory (checked with `psutil.Process().memory_info().rss`) and that each chunk reports correct `participant_id` and `status`.

- [ ] T007 [P0] Create `code/config.py` exposing constants such as `RAW_DIR`, `PROCESSED_DIR`, `ARTIFACTS_DIR`, and `EXPECTED_FEATURE_COLUMNS` (the ordered list of the 30 microstate feature names).  
  **Path**: `code/config.py`.  
  **Verification**: `tests/unit/test_config.py` checks that `len(EXPECTED_FEATURE_COLUMNS) == 30` and that every name matches an entry in `contracts/features.schema.yaml`.

---

## Phase 1 – Data ingestion, preprocessing, and feature‑matrix validation (User Story 1, P1)

- [ ] T008 [P1] Implement the full preprocessing pipeline in `code/preprocessing.py` and produce a validated feature matrix `data/processed/feature_matrix.csv`. Steps include:  
  1. Stream raw EEG via the `DataChunk` loader.  
  2. Re‑reference to average mastoids.  
  3. Apply a zero‑phase FIR band‑pass filter (1–40 Hz).  
  4. Perform FastICA and automatically discard components correlated with EOG or with high kurtosis.  
  5. Exclude participants with **< 4 min** of clean data after ICA (log a warning via the project logger).  
  6. Segment the cleaned data into the canonical four microstate maps (A‑D) and extract the exact 30 features (4 mean durations, 4 occurrence rates, 16 transition probabilities, 6 spectral‑power bands).  
  7. Assemble a per‑participant row and write `data/processed/feature_matrix.csv` (columns = `participant_id`, `heat_pain_threshold`, optional covariates, plus the 30 feature columns).  
  **Paths**: `code/preprocessing.py`, `data/processed/feature_matrix.csv`.  
  **Verification**:  
  * `tests/unit/test_preprocessing.py` loads a synthetic EEG file, runs the feature‑extraction routine, and asserts that the returned `pandas.DataFrame` has exactly 30 feature columns, no NaNs, and correct column names.  
  * `tests/integration/test_full_preprocess.py` runs the pipeline on a 5‑participant real subset and checks that `feature_matrix.csv` exists, the header matches `config.EXPECTED_FEATURE_COLUMNS`, and `df.isna().sum().sum() == 0`.

- [ ] T009 [P1] Add schema‑validation for the generated CSV.  
  1. Create `tests/unit/test_feature_matrix_schema.py` that validates each row of `data/processed/feature_matrix.csv` against `contracts/dataset.schema.yaml` using the `jsonschema` library.  
  2. Ensure the CI runs this test and records its JUnit log as `artifacts/test_feature_matrix_schema.xml`.  
  **Paths**: `tests/unit/test_feature_matrix_schema.py`, `artifacts/test_feature_matrix_schema.xml`.  
  **Verification**: The test must exit with code 0; any schema violation causes CI failure.

- [ ] T016 [P1] Add schema‑validation for individual microstate feature objects.  
  1. Create `tests/unit/test_microstate_feature_schema.py` that validates each `MicrostateFeature` JSON object against `contracts/features.schema.yaml`.  
  2. Run this test in CI and capture its JUnit log as `artifacts/test_microstate_feature_schema.xml`.  
  **Paths**: `tests/unit/test_microstate_feature_schema.py`, `artifacts/test_microstate_feature_schema.xml`.  
  **Verification**: Test exits 0; violations fail CI.

---

## Phase 2 – Model training, nested CV, permutation test, bootstrap CI, and empirical p‑value (User Story 2, P2)

- [ ] T010 [P2] Implement the complete modeling workflow in `code/modeling.py` and orchestrate it from `code/main.py`. The workflow must:  
  1. Train an Elastic Net regression (`α = 0.5`) with nested 5‑fold cross‑validation; inner CV tunes `l1_ratio`.  
  2. Provide a function `global_permutation_test` (see T011) that shuffles `heat_pain_threshold` **once per outer‑CV iteration**, runs the same nested CV for **1 000** permutations, and returns the null‑distribution of mean Pearson r.  
  3. Compute a bootstrap confidence interval (`bootstrap_ci`) with **200** resamples of the outer‑fold r values.  
  4. Compute the empirical p‑value (`compute_empirical_pvalue`) as the proportion of permuted r ≥ observed r.  
  5. Write `artifacts/model_result.json` containing `pearson_r`, `mae`, `p_value`, `ci_lower`, `ci_upper`, `n_permutations`, `n_bootstrap`.  
  6. Write `artifacts/bootstrap_ci.json` with keys `ci_lower` and `ci_upper`.  
  **Paths**: `code/modeling.py`, `code/main.py`, `artifacts/model_result.json`, `artifacts/bootstrap_ci.json`.  
  **Verification**:  
  * `tests/unit/test_modeling_cv.py` runs `train_nested_cv` on a small synthetic dataset, asserts that `α` is 0.5, that required keys are present, and that outputs are floats.  
  * `tests/integration/test_permutation.py` runs `global_permutation_test` on a modest synthetic dataset, asserts the returned array length is 1 000, and that a `max_permutations=5` guard works for a quick sanity check.  
  * `tests/unit/test_bootstrap.py` verifies that `bootstrap_ci` returns numeric bounds (both non‑null) and that `artifacts/bootstrap_ci.json` contains those numbers.  
  * `tests/unit/test_pvalue.py` supplies a synthetic null distribution, calls `compute_empirical_pvalue`, and asserts `0 ≤ p_value ≤ 1` and that `model_result.json` contains the same `p_value`.

- [ ] T011 [P2] Expose the exact symbol required by the specification. In `code/modeling.py` add:  

  ```python
  def global_permutation_test(*args, **kwargs):
      return run_global_permutation_test(*args, **kwargs)
  ```  

  **Path**: `code/modeling.py`.  
  **Verification**: `tests/unit/test_global_permutation_alias.py` imports `global_permutation_test` and checks that its output matches `run_global_permutation_test` for a deterministic small input.

- [ ] T017 [P2] Implement Elastic Net convergence fallback (FR‑003 edge case).  
  1. In the training routine, set `max_iter=1000`; if convergence fails, automatically increase to `max_iter=5000` and retry.  
  2. If it still fails, raise a clear `RuntimeError` with message “Elastic Net failed to converge after max iterations”.  
  3. Add unit test `tests/unit/test_elastic_net_fallback.py` that forces non‑convergence (e.g., by providing ill‑conditioned data) and verifies the fallback logic and error raising.  
  **Paths**: `code/modeling.py` (fallback implementation), `tests/unit/test_elastic_net_fallback.py`.  
  **Verification**: Test passes and CI records its JUnit log as `artifacts/test_elastic_net_fallback.xml`.

---

## Phase 3 – Statistical diagnostics & sensitivity analyses (User Story 3, P3)

- [ ] T012 [P3] Implement a comprehensive diagnostics module in `code/diagnostics.py` that generates all required reports and artifacts:  
  1. Permutation importance for each of the 30 predictors (10 repeats per predictor, average drop in Pearson r).  
  2. Coefficient‑wise Wald p‑values and apply **Benjamini‑Hochberg FDR** correction.  
  3. Variance Inflation Factors for the full predictor set using `statsmodels.stats.outliers_influence.variance_inflation_factor`.  
  4. Median‑split sensitivity sweep for cutoffs `{median‑0.1, median‑0.05, median, median+0.05, median+0.1}` (°C) – compute Cohen’s d for the top‑5 predictive features and write `artifacts/median_sensitivity.csv`.  
  5. Elastic‑Net `α`‑sweep (`α ∈ {0.0, 0.05, …, 1.0}` – 21 values) with inner CV, record outer‑fold R², and write `artifacts/alpha_sweep.csv`.  
  6. Write `artifacts/diagnostics.csv` with columns  
     `feature_name, coefficient, importance_score, p_value_raw, p_value_fdr, vif, is_significant, is_collinear`.  
  7. Compile `artifacts/diagnostics_report.md` containing:  
     * Table of FDR‑adjusted coefficient p‑values (highlighting any < 0.05).  
     * Table of VIF values with a “⚠️” flag for any > 10.  
     * The median‑split Cohen’s d table.  
     * The α‑sweep R² curve (markdown table).  
     * Explicit statement of the top predictive feature’s FDR‑adjusted p‑value.  
  **Paths**: `code/diagnostics.py`, `artifacts/diagnostics.csv`, `artifacts/median_sensitivity.csv`, `artifacts/alpha_sweep.csv`, `artifacts/diagnostics_report.md`.  
  **Verification**:  
  * `tests/unit/test_diagnostics.py` creates a synthetic design matrix with a known collinear column, runs the diagnostics, and asserts that `diagnostics.csv` has 30 rows, at least one `p_value_fdr < 0.05` when appropriate, and that the collinear column is flagged (`vif > 10`).  
  * `tests/unit/test_median_sensitivity.py` checks that `median_sensitivity.csv` has five rows and numeric Cohen’s d values.  
  * `tests/unit/test_alpha_sweep.py` ensures `alpha_sweep.csv` has 21 rows and numeric R² entries.  
  * `tests/integration/test_diagnostics_report.py` runs the full diagnostics on a reduced dataset, asserts that `diagnostics_report.md` contains the three required sections and highlights at least one significant feature.

- [ ] T013 [P3] Add a unit test for the empirical‑p‑value function.  
  **Path**: `tests/unit/test_pvalue.py`.  
  **Verification**: The test imports `compute_empirical_pvalue`, feeds a synthetic null distribution (e.g., 1 000 values drawn from a normal centered at 0), and asserts that the returned `p_value` lies in `[0,1]` and that `artifacts/model_result.json` contains the field `p_value` with the same numeric value.

- [ ] T014 [P3] Add a unit test for the bootstrap confidence‑interval function and ensure the generated artifact contains real numbers.  
  **Path**: `tests/unit/test_bootstrap.py`.  
  **Verification**: The test runs `bootstrap_ci` on a small set of r values, asserts that the returned dictionary has keys `ci_lower` and `ci_upper` with non‑null floats, and checks that `artifacts/bootstrap_ci.json` stores those exact numbers (matching the function output).

- [ ] T018 [P3] Record total pipeline execution time and enforce the 6‑hour limit.  
  1. In `code/utils.py` add `start_timer()` and `stop_timer()` that write elapsed seconds to `artifacts/runtime_log.json`.  
  2. Create `tests/unit/test_runtime_limit.py` that runs a lightweight end‑to‑end demo (using the `--sample 5` flag) and asserts the recorded runtime ≤ 21600 seconds.  
  **Paths**: `code/utils.py`, `tests/unit/test_runtime_limit.py`, `artifacts/runtime_log.json`.  
  **Verification**: CI executes the test; failure if runtime exceeds the limit.

---

## Phase 4 – Documentation, demonstration, and artifact bookkeeping (User Story 4, P4)

- [ ] T015 [P4] Finalise project documentation and produce a reproducible end‑to‑end demonstration:  
  1. Write `quickstart.md` with step‑by‑step usage instructions, referencing the CLI command for a small subset (`python -m code.main --sample 5`).  
  2. Write a concise `README.md` that lists the required Python version (≥ 3.11), installation steps (`pip install -r requirements.txt`), a minimal command‑line example, and the main output locations (`data/processed/feature_matrix.csv`, `artifacts/model_result.json`, `artifacts/diagnostics_report.md`).  
  3. Execute an **end‑to‑end demo** on the provided 5‑participant real subset (`data/raw/sample/`) via `python -m code.main --sample 5`. The run must produce:  
     * `data/processed/feature_matrix.csv` (30 feature columns, no NaNs).  
     * `artifacts/model_result.json` (containing `pearson_r`, `mae`, `p_value`, CI).  
     * `artifacts/diagnostics_report.md`.  
  4. Record SHA‑256 hashes of all major artifacts (`feature_matrix.csv`, `model_result.json`, `diagnostics_report.md`, `bootstrap_ci.json`) in a project‑owned file `artifacts/artifact_hashes.yaml`.  
  5. Verify the hash‑recording step with `tests/unit/test_hash_recording.py`, which reads the YAML file, confirms entries for each artifact, and checks that the stored hash matches the actual file content.  
  **Paths**: `quickstart.md`, `README.md`, `artifacts/artifact_hashes.yaml`, `artifacts/demo_end_to_end.log`.  
  **Verification**: CI runs the demo, asserts the three output files exist and are non‑empty, checks that `model_result.json["p_value"]` is a number between 0 and 1, runs `tests/unit/test_hash_recording.py`, and passes `markdownlint` on `quickstart.md` and `README.md`.
