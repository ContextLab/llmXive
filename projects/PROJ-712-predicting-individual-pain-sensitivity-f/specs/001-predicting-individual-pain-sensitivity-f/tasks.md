# Tasks: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts, and the existing code base.  
**Goal**: Deliver a reproducible end‑to‑end pipeline that (1) ingests the OpenNeuro **ds003542** dataset, (2) extracts the 30 microstate‑derived features per participant, (3) trains an Elastic‑Net regression model with nested 5‑fold cross‑validation, (4) performs the required statistical validation (permutation test, bootstrap CI, FDR, VIF, sensitivity sweeps), and (5) produces the final diagnostics report and documentation. All functional requirements **FR‑001 – FR‑007** and success criteria **SC‑001 – SC‑005** must be satisfied and verifiable by the CI tests.

---

## Phase 0 – Project scaffolding (must be complete before any scientific work)

- [ ] **T001** [P0] Create the required project‑owned directory hierarchy and a helper script `scripts/create_dirs.sh` that runs  

  ```bash
  mkdir -p data/raw data/processed artifacts code tests scripts
  ```  

  **Path(s)**: `data/raw/`, `data/processed/`, `artifacts/`, `code/`, `tests/`, `scripts/create_dirs.sh`.  
  **Verification**: `tests/integration/test_structure.py` asserts that each of the six directories exists after the script exits with code 0.

- [X] **T002** Initialise a Python 3.11 project and add a pinned `requirements.txt` containing at least `mne`, `scikit-learn`, `numpy`, `pandas`, `scipy`, `statsmodels`, `joblib`, `pyyaml`.  
  **Path**: `requirements.txt`.  
  **Verification**: CI step runs `pip install -r requirements.txt`; a unit test checks that each required package appears with a version specifier.

- [X] **T003** Configure linting (`ruff`) and formatting (`black`) via `pyproject.toml`.  
  **Path**: `pyproject.toml`.  
  **Verification**: CI runs `ruff check .` and `black --check .`; both must return exit‑code 0.

- [X] **T004** [P0] Implement `code/utils.py` with:  
  * deterministic seed pinning (`np.random.seed(42)`, `random.seed(42)`),  
  * a lightweight logger that writes to `artifacts/log.txt`,  
  * helper `record_artifact_hash(filepath)` that computes a SHA‑256 hash and returns it.  
  **Path**: `code/utils.py`.  
  **Verification**: `tests/unit/test_utils.py` checks that two identical files yield identical hashes and that the logger creates `artifacts/log.txt` containing a timestamped entry.

- [X] **T005** Add `scripts/pre-run-validation.sh` that executes `python -m code.utils --validate-citations`. The script exits non‑zero if any required citation is missing.  
  **Path**: `scripts/pre-run-validation.sh`.  
  **Verification**: CI runs the script; a missing citation aborts the pipeline.

- [X] **T006** Implement `code/data_loader.py` with a `DataChunk` class that streams OpenNeuro **ds003542** EEG files via `numpy.memmap` (or MNE’s `preload=False`). The loader yields chunk objects so that peak RAM stays ≤ 6 GB.  
  **Verification**: `tests/integration/test_data_loader.py` asserts that processing the full dataset never exceeds 6 GB of resident memory (checked via `psutil`).

- [X] **T007** Create `code/config.py` exposing constants such as `RAW_DIR`, `PROCESSED_DIR`, `ARTIFACTS_DIR`, and `EXPECTED_FEATURE_COLUMNS` (the ordered list of the 30 microstate feature names).  
  **Verification**: `tests/unit/test_config.py` checks that `len(EXPECTED_FEATURE_COLUMNS) == 30` and that every name matches the schema in `contracts/features.schema.yaml`.

---

## Phase 1 – Data ingestion & preprocessing (User Story 1, P1)

- [ ] **T008** [P1] Implement the full preprocessing pipeline in `code/preprocessing.py`:   <!-- FAILED-IN-EXECUTION: code/preprocess_execution.yaml exit=-1 --> <!-- FAILED-IN-EXECUTION: code/preprocess_execution.yaml exit=-1 -->
  1. Stream raw EEG via the `DataChunk` loader.  
  2. Re‑reference to average mastoids.  
  3. Apply a zero‑phase FIR band‑pass filter (1–40 Hz).  
  4. Perform ICA (FastICA) and automatically discard components correlated with EOG or exhibiting high kurtosis.  
  5. Exclude participants with **< 4 min** of clean data after ICA (log a warning via the project logger).  
  6. Segment the cleaned data into the canonical four microstate maps (A‑D) and extract the **exact 30 features** (4 mean durations, 4 occurrence rates, 16 transition probabilities, 6 spectral‑power bands).  
  7. Assemble a per‑participant row and write `data/processed/feature_matrix.csv` (columns = participant_id, heat_pain_threshold, age, gender, valid_eeg_minutes, plus the 30 feature columns).  
  **Path(s)**: `code/preprocessing.py`, `data/processed/feature_matrix.csv`.  
  **Verification**:  
  * `tests/unit/test_preprocessing.py` loads a synthetic EEG file, runs `extract_microstate_features`, and asserts the returned `pandas.DataFrame` has exactly 30 feature columns, no NaNs, and correct column names.  
  * `tests/integration/test_full_preprocess.py` runs the pipeline on a 5‑participant real subset and checks that `feature_matrix.csv` exists, the header matches `config.EXPECTED_FEATURE_COLUMNS`, and `df.isna().sum().sum() == 0`.

- [ ] **T009** [P1] Validate `data/processed/feature_matrix.csv` against `contracts/dataset.schema.yaml` using `jsonschema`.  
  **Verification**: `tests/unit/test_feature_matrix_schema.py` loads the CSV, converts rows to JSON‑compatible dicts, validates against the schema, and fails the CI if any violation is found.

---

## Phase 2 – Model training & validation (User Story 2, P2)

- [X] **T010** [P2] Implement `code/modeling.py::train_nested_cv` that performs **nested 5‑fold cross‑validation** using **Elastic Net** with **α = 0.5** (fixed) and tunes only `l1_ratio` inside the inner loop. The function returns a dictionary containing at least `pearson_r_mean`, `mae_mean`, and `r_per_fold` (list of outer‑fold Pearson r).  
  **Path**: `code/modeling.py`.  
  **Verification**: `tests/unit/test_modeling_cv.py` calls the function on a small synthetic dataset, asserts that α is 0.5, and checks that the required keys are present and are floats.

- [ ] **T011** [P2] Implement `code/modeling.py::global_permutation_test` that builds the **null distribution** of mean Pearson r by:  
  1. For each of **1 000 permutations**, shuffle the `heat_pain_threshold` labels **once per outer CV iteration** (i.e., before the nested CV loop of that permutation).  
  2. Run the same nested CV as in T010 on the permuted labels and store the resulting mean r.  
  3. Enforce a runtime guard `max_permutations=1000`; if the guard is triggered the function aborts with a clear error.  
  **Verification**: `tests/integration/test_permutation.py` runs the function on a modest synthetic dataset, asserts that the returned array length is 1 000, and confirms that setting `max_permutations=5` triggers the early‑exit guard.

- [ ] **T012** [P2] Implement `code/modeling.py::bootstrap_ci` that, given the observed outer‑fold r values, draws **200 bootstrap resamples**, computes the 2.5 th and 97.5 th percentiles, and returns a tuple `(ci_lower, ci_upper)`. The function includes a wall‑time guard that aborts if the projected total runtime would exceed **6 hours**; in that case it logs a warning to `artifacts/log.txt`.  
  **Artifact**: `artifacts/bootstrap_ci.json` with keys `ci_lower` and `ci_upper`.  
  **Verification**: `tests/unit/test_bootstrap.py` uses a deterministic random seed to verify that the function returns numeric bounds and that a mocked timer triggers the guard when the projected runtime > 6 h.

- [ ] **T013** [P2] Implement `code/modeling.py::compute_empirical_pvalue` that:  
  1. Receives the observed mean r, the null distribution from T011, the MAE from T010, and the CI from T012.  
  2. Computes the empirical p‑value as the proportion of null r ≥ observed r.  
  3. Writes `artifacts/model_result.json` containing the fields `pearson_r`, `mae`, `p_value`, `ci_lower`, `ci_upper`, `n_permutations`, `n_bootstrap`.  
  **Verification**: `tests/unit/test_pvalue.py` supplies a synthetic null distribution, calls the function, and asserts that `0 ≤ p_value ≤ 1` and that the JSON file contains all required keys with numeric values.

- [ ] **T014** [P2] Extend `code/main.py` to orchestrate the full pipeline:  
  * Load data via `data_loader`.  
  * Run preprocessing (`T008`).  
  * Train the model (`T010`).  
  * Perform the permutation test (`T011`).  
  * Compute bootstrap CI (`T012`).  
  * Compute empirical p‑value and write `model_result.json` (`T013`).  
  * Record SHA‑256 hashes of `feature_matrix.csv`, `model_result.json`, and `bootstrap_ci.json` via `utils.record_artifact_hash`.  
  * Log total wall‑clock duration to `artifacts/runtime_log.json` and assert that it is **< 6 hours** (SC‑005).  
  **Verification**: CI runs `python -m code.main --sample 5` on the 5‑participant subset and checks that the three JSON/CSV artifacts exist, that `runtime_log.json["total_seconds"] < 21600`, and that the hash‑recording entries are present in `artifacts/artifact_hashes.yaml`.

---

## Phase 3 – Statistical diagnostics & sensitivity analyses (User Story 3, P3)

- [ ] **T015** [P3] Implement `code/diagnostics.py` that, given the trained Elastic Net model and the full feature matrix, computes:  
  1. **Permutation importance** for each of the 30 predictors (10 repeats per predictor, average drop in r).  
  2. **Coefficient‑wise p‑values** via a Wald‑type approximation (or bootstrapped SE) and applies **Benjamini‑Hochberg FDR** correction.  
  3. **Variance Inflation Factors** for the full predictor set using `statsmodels.stats.outliers_influence.variance_inflation_factor`.  
  The function writes `artifacts/diagnostics.csv` with columns  
  `feature_name, coefficient, importance_score, p_value_raw, p_value_fdr, vif, is_significant, is_collinear`.  
  **Verification**: `tests/unit/test_diagnostics.py` creates a synthetic design matrix with a known collinear column, runs the function, and asserts that: (a) the CSV has 30 rows, (b) at least one `p_value_fdr < 0.05` when appropriate, and (c) the collinear column is flagged with `vif > 10`.

- [ ] **T016** [P3] Perform a **median‑split effect‑size sensitivity sweep** for the continuous outcome: for cutoffs `{median‑0.1, median‑0.05, median, median+0.05, median+0.1}` (in °C) compute Cohen’s d for the top‑5 predictive features and store results in `artifacts/median_sensitivity.csv`.  
  **Verification**: `tests/unit/test_median_sensitivity.py` checks that the CSV has five rows (one per offset) and that all d‑values are numeric.

- [ ] **T017** [P3] Conduct an **α‑sweep** of Elastic  Net regularization strength with α ∈ {0.0, 0.05, 0.10, …, 1.0} (21 values). For each α, tune `l1_ratio` as in T010, record outer‑fold R², and write `artifacts/alpha_sweep.csv`.  
  **Verification**: `tests/unit/test_alpha_sweep.py` ensures the CSV has 21 rows and that R² values are numeric.

- [ ] **T018** [P3] Generate `artifacts/diagnostics_report.md` that includes:  
  * A table of **FDR‑adjusted coefficient p‑values** (highlighting significant features).  
  * A table of **VIF values** with a “⚠️” flag for any > 10.  
  * The median‑split **Cohen’s d** results from T016.  
  * The α‑sweep **R²** curve from T017.  
  * An explicit statement of the top predictive feature’s FDR‑adjusted p‑value.  
  No logistic‑regression AUC/accuracy sections are present.  
  **Verification**: `tests/integration/test_diagnostics_report.py` runs the full diagnostics pipeline on a reduced dataset, asserts that `diagnostics_report.md` contains the three required sections and at least one significant feature highlighted.

---

## Phase 4 – Documentation, demonstration & artifact bookkeeping

- [ ] **T020** [P4] Create `quickstart.md` with step‑by‑step usage instructions, referencing the CLI command for a small subset (`python -m code.main --sample 5`).  
  **Verification**: `tests/unit/test_quickstart.py` parses the file, executes the example command on a synthetic dataset, and confirms successful pipeline execution.

- [ ] **T021** [P4] Write a concise `README.md` that:  
  1. Lists the required Python version (≥ 3.11).  
  2. Provides installation instructions (`pip install -r requirements.txt`).  
  3. Shows a minimal command‑line example to run the full pipeline on a small subset (`python -m code.main --sample 5`).  
  4. Points to the main output locations (`data/processed/feature_matrix.csv`, `artifacts/model_result.json`, `artifacts/diagnostics_report.md`).  
  **Verification**: CI runs `markdownlint` and a custom script that extracts the “Usage” code block, executes it on a tiny synthetic dataset, and confirms successful completion.

- [ ] **T022** [P4] Run an **end‑to‑end demonstration** on the provided 5‑participant real subset (`data/raw/sample/`). The run must produce:  
  * `data/processed/feature_matrix.csv` (30 feature columns, no NaNs).  
  * `artifacts/model_result.json` (containing r, mae, p‑value, CI).  
  * `artifacts/diagnostics_report.md`.  
  CI job `demo_end_to_end` executes `python -m code.main --sample 5` and asserts the existence and non‑emptiness of the three files; it also checks that `model_result.json["p_value"]` is a number between 0 and 1.

- [ ] **T023** [P4] Record SHA‑256 hashes of all major artifacts (`feature_matrix.csv`, `model_result.json`, `diagnostics_report.md`, `bootstrap_ci.json`) in a project‑owned file `artifacts/artifact_hashes.yaml`.  
  **Verification**: `tests/unit/test_hash_recording.py` reads the YAML file and confirms entries for each of the four artifacts, verifying that the stored hash matches the actual file content.
