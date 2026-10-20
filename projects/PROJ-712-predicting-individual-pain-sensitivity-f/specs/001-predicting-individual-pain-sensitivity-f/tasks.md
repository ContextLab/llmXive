# Tasks: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts, and the existing code base.  
**Goal**: Deliver a reproducible end‑to‑end pipeline that (1) ingests the OpenNeuro **ds003542** dataset, (2) extracts the 30 microstate‑derived features per participant, (3) trains an Elastic‑Net regression model with nested 5‑fold cross‑validation, (4) performs the required statistical validation (permutation test, bootstrap CI, FDR, VIF, sensitivity sweeps), and (5) produces the final diagnostics report and documentation. All functional requirements **FR‑001 – FR‑007** and success criteria **SC‑001 – SC‑005** must be satisfied and verifiable by the CI tests.

---

## Phase 0 – Project scaffolding (must be complete before any scientific work)

- [ ] **T001** [P0] Create the required project‑owned directory hierarchy and a helper script `scripts/create_dirs.sh` that runs  

  ```bash
  mkdir -p data/raw data/processed artifacts code tests scripts
  ```  

  **Paths**: `data/raw/`, `data/processed/`, `artifacts/`, `code/`, `tests/`, `scripts/create_dirs.sh`.  
  **Verification**:  
  * Run `scripts/create_dirs.sh` in CI and capture its stdout/stderr.  
  * Execute `tests/integration/test_structure.py` which asserts that each of the six directories exists after the script exits with code 0.  
  * CI must store the test log (e.g., `artifacts/test_structure.log`) and the task is considered passed when the log shows exit 0 and all assertions succeed.

- [ ] **T002** [P0] Initialise a Python 3.11 project and add a pinned `requirements.txt` containing at least `mne`, `scikit-learn`, `numpy`, `pandas`, `scipy`, `statsmodels`, `joblib`, `pyyaml`.  
  **Path**: `requirements.txt`.  
  **Verification**: CI runs `pip install -r requirements.txt`; a unit test checks that each required package appears with a version specifier.

- [ ] **T003** [P0] Configure linting (`ruff`) and formatting (`black`) via `pyproject.toml`.  
  **Path**: `pyproject.toml`.  
  **Verification**: CI runs `ruff check .` and `black --check .`; both must return exit 0.

- [ ] **T004** [P0] Implement `code/utils.py` with:  
  * deterministic seed pinning (`np.random.seed(42)`, `random.seed(42)`),  
  * a lightweight logger that writes to `artifacts/log.txt`,  
  * helper `record_artifact_hash(filepath)` that computes a SHA‑256 hash and returns it.  
  **Path**: `code/utils.py`.  
  **Verification**: `tests/unit/test_utils.py` checks that two identical files yield identical hashes and that the logger creates `artifacts/log.txt` containing a timestamped entry.

- [ ] **T005** [P0] Add `scripts/pre-run-validation.sh` that executes `python -m code.utils --validate-citations`. The script exits non‑zero if any required citation is missing.  
  **Path**: `scripts/pre-run-validation.sh`.  
  **Verification**: CI runs the script; a missing citation aborts the pipeline (exit ≠ 0).

- [ ] **T006** [P0] Implement `code/data_loader.py` with a `DataChunk` class that streams OpenNeuro **ds003542** EEG files via `numpy.memmap` (or MNE’s `preload=False`). The loader yields chunk objects so that peak RAM stays ≤ 6 GB.  
  **Verification**: `tests/integration/test_data_loader.py` asserts that processing the full dataset never exceeds 6 GB of resident memory (checked with `psutil`).

- [ ] **T007** [P0] Create `code/config.py` exposing constants such as `RAW_DIR`, `PROCESSED_DIR`, `ARTIFACTS_DIR`, and `EXPECTED_FEATURE_COLUMNS` (the ordered list of the 30 microstate feature names).  
  **Verification**: `tests/unit/test_config.py` checks that `len(EXPECTED_FEATURE_COLUMNS) == 30` and that every name matches the schema in `contracts/features.schema.yaml`.

---

## Phase 1 – Data ingestion, preprocessing, and feature‑matrix validation (User Story 1, P1)

- [ ] **T008** [P1] Implement the full preprocessing pipeline in `code/preprocessing.py` and produce a validated feature matrix:  

  1. Stream raw EEG via the `DataChunk` loader.  
  2. Re‑reference to average mastoids.  
  3. Apply a zero‑phase FIR band‑pass filter (1–40 Hz).  
  4. Perform ICA (FastICA) and automatically discard components correlated with EOG or exhibiting high kurtosis.  
  5. Exclude participants with **< 4 min** of clean data after ICA (log a warning via the project logger).  
  6. Segment the cleaned data into the canonical four microstate maps (A‑D) and extract the exact 30 features (4 mean durations, 4 occurrence rates, 16 transition probabilities, 6 spectral‑power bands).  
  7. Assemble a per‑participant row and write `data/processed/feature_matrix.csv` (columns = `participant_id`, `heat_pain_threshold`, optional covariates, plus the 30 feature columns).  

  **Paths**: `code/preprocessing.py`, `data/processed/feature_matrix.csv`.  
  **Verification**:  
  * `tests/unit/test_preprocessing.py` loads a synthetic EEG file, runs the feature‑extraction routine, and asserts the returned `pandas.DataFrame` has exactly 30 feature columns, no NaNs, and correct column names.  
  * `tests/integration/test_full_preprocess.py` runs the pipeline on a 5‑participant real subset and checks that `feature_matrix.csv` exists, the header matches `config.EXPECTED_FEATURE_COLUMNS`, and `df.isna().sum().sum() == 0`.  
  * `tests/unit/test_feature_matrix_schema.py` validates each row of `feature_matrix.csv` against `contracts/dataset.schema.yaml` using `jsonschema`; the CI fails if any violation is found.

---

## Phase 2 – Model training, nested CV, permutation test, bootstrap CI, and empirical p‑value (User Story 2, P2)

- [ ] **T010** [P2] Implement the complete modeling workflow in `code/modeling.py` and orchestrate it from `code/main.py`:  

  1. **Elastic Net regression** (`α = 0.5`) with nested 5‑fold cross‑validation; inner CV tunes `l1_ratio`.  
  2. **Global permutation test** – expose a function named `global_permutation_test` (alias to the existing implementation) that shuffles `heat_pain_threshold` **once per outer‑CV iteration**, runs the same nested CV for each of **1 000** permutations, and returns the null‑distribution of mean Pearson r.  
  3. **Bootstrap confidence interval** – `bootstrap_ci` draws **200** resamples of the outer‑fold r values and returns the 2.5 th and 97.5 th percentiles.  
  4. **Empirical p‑value** – `compute_empirical_pvalue` calculates the proportion of permuted r ≥ observed r and writes `artifacts/model_result.json` containing `pearson_r`, `mae`, `p_value`, `ci_lower`, `ci_upper`, `n_permutations`, `n_bootstrap`.  
  5. Write `artifacts/bootstrap_ci.json` with keys `ci_lower` and `ci_upper`.  

  **Paths**: `code/modeling.py`, `code/main.py`, `artifacts/model_result.json`, `artifacts/bootstrap_ci.json`.  
  **Verification**:  
  * `tests/unit/test_modeling_cv.py` runs `train_nested_cv` on a small synthetic dataset, asserts that `α` is 0.5, that required keys are present, and that outputs are floats.  
  * `tests/integration/test_permutation.py` runs `global_permutation_test` on a modest synthetic dataset, asserts the returned array length is 1 000, and that a guard `max_permutations=5` triggers an early‑exit error.  
  * `tests/unit/test_bootstrap.py` verifies that `bootstrap_ci` returns numeric bounds and that a mocked timer triggers the 6‑hour guard, logging a warning to `artifacts/log.txt`.  
  * `tests/unit/test_pvalue.py` supplies a synthetic null distribution, calls `compute_empirical_pvalue`, and asserts `0 ≤ p_value ≤ 1` and that all required fields exist in `model_result.json`.

---

## Phase 3 – Statistical diagnostics & sensitivity analyses (User Story 3, P3)

- [ ] **T015** [P3] Implement a comprehensive diagnostics module in `code/diagnostics.py` and generate all required reports:  

  1. **Permutation importance** for each of the 30 predictors (10 repeats per predictor, average drop in Pearson r).  
  2. **Coefficient‑wise p‑values** (Wald‑type or bootstrapped SE) and apply **Benjamini‑Hochberg FDR** correction.  
  3. **Variance Inflation Factors** for the full predictor set using `statsmodels.stats.outliers_influence.variance_inflation_factor`.  
  4. **Median‑split sensitivity sweep** – for cutoffs `{median‑0.1, median‑0.05, median, median+0.05, median+0.1}` (°C) compute Cohen’s d for the top‑5 predictive features and write `artifacts/median_sensitivity.csv`.  
  5. **α‑sweep** – vary Elastic Net regularization strength `α ∈ {0.0, 0.05, …, 1.0}` (21 values), tune `l1_ratio` as in the main model, record outer‑fold R², and write `artifacts/alpha_sweep.csv`.  
  6. Write `artifacts/diagnostics.csv` with columns  
     `feature_name, coefficient, importance_score, p_value_raw, p_value_fdr, vif, is_significant, is_collinear`.  
  7. Compile `artifacts/diagnostics_report.md` containing:  
     * Table of FDR‑adjusted coefficient p‑values (highlighting any < 0.05).  
     * Table of VIF values with a “⚠️” flag for any > 10.  
     * The median‑split Cohen’s d table.  
     * The α‑sweep R² curve (as a markdown table).  
     * Explicit statement of the top predictive feature’s FDR‑adjusted p‑value.  

  **Verification**:  
  * `tests/unit/test_diagnostics.py` creates a synthetic design matrix with a known collinear column, runs the diagnostics, and asserts that the CSV has 30 rows, at least one `p_value_fdr < 0.05` when appropriate, and that the collinear column is flagged with `vif > 10`.  
  * `tests/unit/test_median_sensitivity.py` checks that `median_sensitivity.csv` has five rows and numeric d‑values.  
  * `tests/unit/test_alpha_sweep.py` ensures `alpha_sweep.csv` has 21 rows and numeric R² entries.  
  * `tests/integration/test_diagnostics_report.py` runs the full diagnostics on a reduced dataset, asserts that `diagnostics_report.md` contains the three required sections and highlights at least one significant feature.

---

## Phase 4 – Documentation, demonstration, and artifact bookkeeping (User Story 4, P4)

- [ ] **T020** [P4] Finalise project documentation and produce a reproducible end‑to‑end demonstration:  

  1. Write `quickstart.md` with step‑by‑step usage instructions, referencing the CLI command for a small subset (`python -m code.main --sample 5`).  
  2. Write a concise `README.md` that lists the required Python version (≥ 3.11), installation steps (`pip install -r requirements.txt`), a minimal command‑line example, and the main output locations (`data/processed/feature_matrix.csv`, `artifacts/model_result.json`, `artifacts/diagnostics_report.md`).  
  3. Execute an **end‑to‑end demo** on the provided 5‑participant real subset (`data/raw/sample/`) via `python -m code.main --sample 5`. The run must produce:  
     * `data/processed/feature_matrix.csv` (30 feature columns, no NaNs).  
     * `artifacts/model_result.json` (containing `pearson_r`, `mae`, `p_value`, CI).  
     * `artifacts/diagnostics_report.md`.  
     CI job `demo_end_to_end` asserts existence, non‑emptiness, and that `model_result.json["p_value"]` is a number between 0 and 1.  
  4. Record SHA‑256 hashes of all major artifacts (`feature_matrix.csv`, `model_result.json`, `diagnostics_report.md`, `bootstrap_ci.json`) in a project‑owned file `artifacts/artifact_hashes.yaml`.  
  5. Verify the hash‑recording step with `tests/unit/test_hash_recording.py`, which reads the YAML file, confirms entries for each artifact, and checks that the stored hash matches the actual file content.

  **Verification**: CI runs the demo, checks the three output files, runs the hash‑recording test, and passes `markdownlint` on `quickstart.md` and `README.md`.

--- 

*All tasks are unchecked until their implementation and associated verification tests pass in CI. Checked tasks from the previous iteration that already satisfy their verification criteria are retained as shown.*
