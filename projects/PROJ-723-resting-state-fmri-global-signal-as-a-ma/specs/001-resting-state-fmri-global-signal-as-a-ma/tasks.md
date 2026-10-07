# Tasks: Resting‑State fMRI Global Signal as a Marker of Mind‑Wandering

**Input**: Design documents from `/specs/001-resting-state-fmri-global-signal-as-a-ma/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjusted based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create `code/` directory at repository root
- [X] T001b Create `data/raw/` directory at repository root
- [X] T001c Create `data/processed/` directory at repository root
- [X] T001d Create `tests/` directory at repository root
- [X] T002 Initialize Python project with dependencies from `requirements.txt` (pandas, numpy, scikit-learn, nibabel, requests, pyyaml, statsmodels, scipy)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` to define paths, random seeds, and hyperparameters
- [X] T005 [P] Implement `code/utils.py` for logging, file I/O helpers, and error handling
- [X] T006 [P] Create `code/mwq_scoring.py` to document MWQ version, reverse-scoring rules, and total score calculation (Principle VII)
- [X] T007 Implement `prepare_bids_structure(raw_file_paths: list[str])` function in `code/ingestion.py` to generate BIDS-compatible directory structure logic. **Input**: A list of raw file paths to organize. **Output**: reusable function. Verification: Run on sample subject '100307' from downloaded data, verify `sub-<label>/func/` exists and contains expected `func/` subdirectory. (Phase 0, Step 3)
- [X] T008 Implement `generate_sidecars(subject_metadata: pd.DataFrame)` function in `code/ingestion.py` to create JSON sidecars for fMRI runs. **Input**: A pandas DataFrame containing subject metadata (Subject_ID, TR, voxel_size, pipeline_version). **Output**: reusable function. File pattern: `sub-<label>_task-rest_bold.json`. Required keys: `TR`, `voxel_size`, `pipeline_version`. Verification: Verify file exists and contains valid JSON with required keys. (Phase 0, Step 3)
- [X] T008b [Foundational] Generate `contracts/dataset.schema.yaml` defining the required columns (Subject_ID, global_signal, global_signal_sd, MWQ_Score, Age, Sex, Mean_FD, Mean_DVARS) and data types for validation. Output: `contracts/dataset.schema.yaml`. **Format**: Use JSON schema style within YAML (e.g., `type: float`, `nullable: false`). This artifact is a strict blocking dependency for downstream tasks like T010. Do not start T010 until T008b is complete. (Required by T010).
- [X] T008c [Foundational] [Requires: T008b] Generate `data-model.md` mapping Spec 'Key Entities' (Subject, Run, Model_Result) to the schema defined in `contracts/dataset.schema.yaml`. **Output**: `data-model.md`. **Logic**: Explicitly map each attribute (e.g., `Global_Signal_SD`, `Time_Series`) to the corresponding schema column and type. This task closes the traceability gap between Spec Key Entities and the schema. (FR-001, SC-001)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Metric Computation (Priority: P1) 🎯 MVP

**Goal**: Download HCP data, compute global signal amplitude (SD), and export a clean CSV with predictors and outcomes.

**Independent Test**: Run ingestion script on a small subset of subjects and verify output CSV contains `Subject_ID`, `Global_Signal_SD`, `MWQ_Score`, `Age`, `Sex`, `FD`, `DVARS` with no missing values.

### Implementation for User Story 1

- [X] T009 [US1] Implement data download logic in `code/ingestion.py` using `datasets.load_dataset` with `streaming=True` to fetch HCP resting-state fMRI (minimally preprocessed 4D NIfTI) and MWQ scores. **Constraint**: Must stream data to avoid memory overflow; must NOT use synthetic fallbacks. **Auth**: Check for `HCP_USER` and `HCP_PASS` (or token) environment variables; if missing, raise `FileNotFoundError` with message "HCP credentials missing". **Logic**: Load dataset 'HCP-Release'. Extract column `func/resting_state_bold_4d` for 4D time series. **Constraint**: Do NOT attempt fallback to NIfTI if parquet is unavailable; halt with error. **Output**: raw parquet files or NIfTI files in `data/raw/`. (FR-001)
- [X] T009a [US1] [Requires: T009] Implement column inspection logic in `code/ingestion.py` to verify the presence of `global_signal` or `global_signal_sd` in the fetched stream. **Critical Verification**: If missing, abort with `FATAL: Dataset Mismatch - Required columns not found in verified URL`. Output: Exit code or log entry. (FR-001)
- [X] T009b [US1] [Requires: T009a] Save the fetched raw data to `data/raw/` with checksums recorded in `state/artifact_hashes.yaml`. (FR-001)
- [X] T010 [US1] [Requires: T008b] Implement schema verification in `code/ingestion.py` using `contracts/dataset.schema.yaml`. **Function**: `validate_schema(df: pd.DataFrame, schema_path: str) -> bool`. **Logic**: Wait for T008b output file creation. Load schema, validate DataFrame. If required columns (global_signal, global_signal_sd, etc.) are missing or types mismatch, raise `FATAL: Dataset Mismatch - Schema Validation Failed`. Output: Log or exit code. (FR-001)
- [X] T011 [US1] [Requires: T010] Implement voxel-wise mean time series (global signal) computation per run in `code/ingestion.py`. **Input**: Streaming generator of NIfTI paths. **Logic**: Iterate over streaming 4D NIfTI chunks; compute voxel-wise mean per chunk; accumulate statistics (sum, sum of squares) online to avoid loading full volume. **Output**: Global signal time series per run. (FR-002)
- [X] T012 [US1] [Requires: T011] Implement standard deviation calculation of global signal per run and averaging across runs per subject. **Function**: `compute_global_signal_sd(time_series: np.ndarray) -> float`. **Input**: Output of T011 (time series array). **Output**: Float value appended to subject record. **Verification**: Compare result against a manual calculation on a hardcoded sample array `np.array([1.0, 2.0, 3.0, 4.0])` (SD should be ~1.118) within tolerance 0.0001. (FR-002)
- [X] T013 [US1] [Requires: T012] [Data Hygiene] Implement subject validation logic to join fMRI and MWQ data, excluding unmatched pairs and logging counts and reasons to `data/logs/exclusions.log`. **Artifact**: `data/logs/exclusions.log` with format: `EXCLUSION: reason=pair_missing, subject_id=XXX`. (FR-009)
- [X] T014 [US1] [Requires: T013] [Data Hygiene] Implement motion exclusion logic to filter subjects where **per-subject mean FD** > 0.5mm. **Constraint**: This is a data hygiene exclusion step, NOT a model adjustment. Log exclusion counts AND subject IDs to `data/logs/exclusions.log` with format: `EXCLUSION: reason=high_motion, subject_id=XXX, mean_fd=0.XX`. Output: Filtered dataset. (FR-008)
- [X] T015 [US1] [Requires: T014] [Data Hygiene] Implement zero-variance check to exclude subjects with `global_signal_sd == 0`, raise a warning, and **log the exclusion count** to `data/logs/exclusions.log` with format: `EXCLUSION: reason=zero_variance, subject_id=XXX`. **Output**: Write a summary line `TOTAL_EXCLUDED: N=<count>` to `data/logs/exclusions.log` upon completion. (Edge Cases)
- [X] T016 [US1] [Requires: T015] Generate `data/processed/cleaned_data.csv` containing Subject_ID, Global_Signal_SD, MWQ_Score, Age, Sex, Mean_FD, Mean_DVARS
- [X] T017 [P] [US1] Unit test: Verify global signal SD calculation matches manual calculation on sample data in `tests/test_ingestion.py`
- [X] T018 [P] [US1] Unit test: Verify exclusion logic for missing pairs and high motion subjects in `tests/test_ingestion.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Association Modeling and Baseline Comparison (Priority: P2)

**Goal**: Run ridge regression to predict MWQ from global signal amplitude (adjusted for covariates), compare against null model, and generate report.

**Independent Test**: Run modeling script on synthetic data (r=0.3) and verify out-of-fold Pearson r falls within 0.25–0.35 and null model performance is near zero.

### Implementation for User Story 2

- [X] T019 [US2] [Requires: T016] **Implement and Execute** the primary ridge regression pipeline in `code/modeling.py`. **Function**: `run_ridge_pipeline(data: pd.DataFrame, alpha_grid: list[float], cv_folds: int, seed: int)`. **Logic**: 1. Define nested k-fold CV structure (inner loop for alpha tuning, outer loop for performance). 2. Fit model Y ~ Global_Signal_SD + FD + DVARS + Age + Sex. 3. Run nested CV with `alpha_grid will include a range of regularization parameters spanning multiple orders of magnitude.`. 4. **Save residuals** to `data/processed/residuals.csv` with schema: `Subject_ID, residual_raw, residual_standardized`. 5. **Save results** to `data/results/full_model.json` (containing MAE, r, R², alpha). **Verification**: Assert `residuals.csv` exists and is non-empty. (FR-003, FR-004)
- [X] T021 [US2] [Requires: T019] **Execute** the null distribution generation in `code/modeling.py` by **independently permuting the MWQ score vector** (using `seed=42` for the permutation loop) and running the full nested CV pipeline for each permutation. **Function**: `run_null_permutations(n: int, seed: int)`. **Logic**: Run a FIXED number of N=100 permutations. **Write** the resulting MAE and R² values to `data/results/null_distribution.json` with schema `{"permutations": [{"mae": float, "r2": float},...]}`. **Constraint**: Assert `len(null_distribution) == 100` before calculating p-value. **Verification**: Verify that the calculated p-value is reported with appropriate decimal precision and that the null distribution histogram is saved to `data/results/null_dist.png`. (FR-005, SC-002, Plan-Phase2-Step3)
- [X] T022 [US2] [Requires: T021, T019] Implement empirical p-value calculation: read `data/results/null_distribution.json` and the observed MAE from `data/results/full_model.json` (T019's execution output), then calculate the proportion of null MAEs <= observed MAE (standard convention, SC-002). (FR-005)
- [X] T038 [US2] [FR-005] [SC-002] [Requires: T019] Implement the **Reduced Model Permutation Loop** specifically for the isolation test. **Function**: `run_reduced_model_permutations(n: int, seed: int)`. **Logic**: Create a dedicated function that fits the Reduced Model (Y ~ FD + DVARS + Age + Sex), permutes MWQ, and records R² for N=100 permutations. **Output**: `data/results/reduced_null_r2.json` with schema `{"permutations": [{"r2": float},...]}`. (FR-005, Plan Methodology)
- [X] T023 [US2] [Requires: T019, T038] **Implement Reduced Model Comparison (Isolation Step)**. **Logic**: 1. Fit a **Reduced Model** (Y ~ FD + DVARS + Age + Sex) without GSA. 2. Use the null distribution from T038. 3. Calculate Delta R² (Full R² - Reduced R²) for the observed data. 4. For each permutation in T038, calculate Delta R²_perm (Full_Perms R² - Reduced_Perms R²). 5. Test if the observed Delta R² is significantly different from the distribution of Delta R²_perm (empirical p-value). **Output**: Write results to `data/results/delta_r2.json` containing Delta R², status (significant/not significant), and the p-value. **Fallback**: If Reduced Model fails (e.g., collinearity), output `data/results/delta_r2.json` with schema `{'status': 'failed', 'reason': 'High Collinearity', 'delta_r2': null}` and log 'High Collinearity' and set a flag to trigger narrative change in T025. (Plan Phase 2 Step 3)
- [X] T024 [US2] [Requires: T016] Implement collinearity diagnostics (VIF, GSA-FD correlation) in `code/diagnostics.py`. Input: `data/processed/cleaned_data.csv`. Output: `data/results/diagnostics.json` with VIF values per predictor and a `collinearity_flag` (boolean: true if any VIF > 5). **Logic**: If `collinearity_flag` is true, log a warning and set a flag to trigger narrative change in T025. (Plan Phase 1 Step 3)
- [X] T025 [US2] [Requires: T019, T022, T023, T024] Generate `data/results/model_report.json` containing mean out-of-fold MAE, Pearson r, R², p-value, and Reduced Model stats (**must include `Delta_R2` and `Reduced_Model_R2` keys**). **Logic**: If `collinearity_flag` from T024 is true, set `interpretation_type` to 'Predictive Gain'; otherwise, set to 'Independent Effect'. (Plan Phase 1 Step 3)
- [X] T026 [P] [US2] Unit test: Verify nested CV logic and alpha tuning on synthetic data in `tests/test_modeling.py`
- [X] T027 [P] [US2] Unit test: Verify null model performance is near zero on permuted data in `tests/test_modeling.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Validate findings with alternative metrics (variance vs SD), additional confounds, and regularization parameter sweeps.

**Independent Test**: Run robustness script and verify reported correlation coefficients remain statistically significant across all variants.

### Implementation for User Story 3

- [X] T028 [US3] [Requires: T016, T019] Implement sensitivity analysis in `code/robustness.py` to sweep alpha over a range of small to large values and report MAE variation (FR-006)
- [X] T029 [US3] [Requires: T016, T019] Implement alternative metric analysis in `code/robustness.py` using global-signal variance instead of SD and report Pearson r (FR-007)
- [X] T030 [US3] [Requires: T019, T024] Implement partial correlation analysis controlling for mean FD to verify independence of GSA effect. **Logic**: First, check the `collinearity_flag` in `data/results/diagnostics.json` (T024 output). If `collinearity_flag` is true, **skip execution**, log 'SKIPPED: High Collinearity', and output `data/results/partial_corr.json` with `status: 'skipped'`. If false, proceed: Use the **residuals from the FULL Ridge Regression model (Y ~ GSA + FD + DVARS + Age + Sex)** saved in `data/processed/residuals.csv` (T019 output) to calculate partial correlation. **Operation**: Correlation between residuals of (MWQ ~ Covariates) and residuals of (Global_Signal_SD ~ Covariates). **Fallback**: If `data/processed/residuals.csv` is missing, **skip execution**, log 'SKIPPED: Missing Residuals', and output `data/results/partial_corr.json` with `status: 'skipped'`. **Note**: This is a supplementary robustness check, not the primary verification of FR-003 (which is handled by T019). **Verification**: Calculate and report the p-value. **Output**: Write results to `data/results/partial_corr.json` with keys `p_value`, `status` (values: 'significant' if p < 0.05, else 'null_finding', or 'skipped'), and `method`. **Comparison**: Compare the p-value against the SC-005 baseline (p < 0.05) and report the 'independence status' (met/not met). Do NOT assert p < 0.05; report the actual result and status. (FR-003, SC-005)
- [X] T031 [US3] [Requires: T028, T029, T030] Generate `data/results/robustness_report.json` containing alpha sweep results, variance metric correlation, and partial correlation stats
- [X] T032 [P] [US3] Unit test: Verify alpha sweep results match expected MAE variations in `tests/test_robustness.py`
- [X] T033 [P] [US3] Unit test: Verify variance metric correlation is within ±0.05 of primary SD result in `tests/test_robustness.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Final Validation

**Purpose**: Aggregate results and verify success criteria.

- [X] T012b [US1] [Requires: T016] [Power Analysis] Implement power analysis in `code/diagnostics.py` to calculate Minimum Detectable Effect Size (MDES) for the **actual N**. **Function**: `calculate_power(N: int, alpha: float, power: float) -> dict`. **Logic**: Calculate N = len(df) from `data/processed/cleaned_data.csv`. Calculate MDES. **Output**: Write to `data/results/power_analysis.json` with keys `N`, `MDES`, `power_risk` (boolean). **Constraint**: DO NOT halt the pipeline. Log a non-blocking RISK flag if power is insufficient. Validate 'Assumptions' section regarding sample size. (FR-001, SC-001)
- [X] T034a [P] [US3] [Requires: T025, T031] Aggregate all results into `data/results/final_report.json` (Primary, Null, Robustness). (SC-001 to SC-005)
- [X] T034b [P] [Requires: T034a] **Regenerate** `final_report.json` with `criteria_status` object. **Logic**: Read p-value, correlation, and stability metrics from the aggregated `data/results/final_report.json` (T034a output). **Schema**: Write a JSON object `criteria_status` with keys `SC-001` through `SC-005`. Each entry must contain: `status` (met/not met), `narrative_summary` (string), AND `metrics` (object containing the specific empirical values: `p_value`, `correlation_coefficient`, `mae`, `r_squared` as applicable). **Constraint**: If p-value >= 0.05, explicitly state the null finding in a `narrative_summary` field. Do NOT assert significance; report the actual status. **Thresholds**: SC-001/002: p < 0.05; SC-003: |r_var - r_sd| <= 0.05; SC-004: MAE variation < 10%; SC-005: p < 0.05. **Output**: Add `criteria_status` object with `metrics` and `narrative_summary` string for each SC describing the outcome (e.g., "Significant: p=0.03" or "Null Finding: p=0.12, no evidence of association"). (SC-001 to SC-005)
- [X] T035 [P] [Requires: T034a] Generate visualizations: `data/results/null_dist.png`, `data/results/alpha_sweep.png`, `data/results/corr_matrix.png` using `matplotlib`. **Validation**: Verify all files exist and have non-zero size. (SC-001 to SC-005)
- [X] T036a [P] [Requires: T016] **Generate** a small synthetic test fixture (`data/tests/test_fixture.csv`) with N=10 subjects containing valid columns (Subject_ID, Global_Signal_SD, MWQ_Score, Age, Sex, Mean_FD, Mean_DVARS). **Constraint**: This fixture is for integration testing ONLY and must NOT be used in the real analysis pipeline (T009 forbids synthetic fallbacks). (Test Requirement)
- [X] T036 [P] [Requires: T034a, T036a] Run end-to-end integration test on full pipeline using the **test fixture** from T036a. **Validation**: Verify the test passes and logs are generated. (SC-001 to SC-005)
- [X] T037 [P] [Requires: T019, T025, T031] Create `code/main.py` as the primary pipeline orchestrator. **Logic**: Implement the full pipeline flow: Ingestion (T009-T016) -> Modeling (T019-T025) -> Robustness (T028-T031) -> Reporting (T034a-T034b). **Output**: `code/main.py` runnable as `python code/main.py`. This task proactively implements the orchestrator defined in the plan's Project Structure, ensuring the run-book can invoke it. (Plan Phase 0 Step 1)

---

## Phase 7: Revision & Robustness Fixes (Review Resolution)

**Goal**: Address specific reviewer concerns regarding data integrity, streaming logic, and analysis independence.

- [X] T039 [US1] [Requires: T009] **Refine Streaming Logic**: Update `code/ingestion.py` to explicitly handle chunked iteration over the `streaming=True` dataset. Ensure that the global signal calculation (T011) accumulates statistics (sum, sum of squares) online per chunk to avoid holding the entire 4D time series in RAM. **Constraint**: The script must NOT attempt to load the full dataset into a single numpy array. (FR-001, Plan Phase 0, Data Hygiene)
- [X] T040 [US1] [Requires: T009] **Enforce "Fail Loudly" on Data Fetch**: Remove any `try/except` blocks in `code/ingestion.py` that catch network errors and fallback to `generate_synthetic_*()`. If `datasets.load_dataset` fails to connect or returns an empty stream, the script must raise a `ConnectionError` or `FileNotFoundError` and exit immediately. Verify that no synthetic data generation code is reachable during the ingestion phase. (Constitution Rule: No Synthetic Fallbacks, FR-001)
- [X] T041 [US2] [Requires: T038, T023] **Isolate GSA Effect in Reduced Model**: Refine `code/modeling.py` to ensure the Reduced Model (Y ~ FD + DVARS + Age + Sex) is fitted **independently** of the Full Model during the permutation loop. Verify that the `Delta_R2` calculation in T023 uses the specific R² from the Reduced Model's permutation run, not a cached value from the Full Model run. (Plan Phase 2 Step 3, FR-005)
- [ ] T042 [US2] [Requires: T024, T030] **Dynamic Partial Correlation Logic**: Update `code/robustness.py` (T030) to dynamically read the `collinearity_flag` from `data/results/diagnostics.json` **at runtime**. If the flag is `True`, the script must skip the partial correlation calculation and write `status: 'skipped'` to `data/results/partial_corr.json` without attempting the calculation, preventing numerical instability. (Plan Phase 1 Step 3, Edge Cases)
- [X] T043 [US3] [Requires: T028] **Validate Alpha Sweep Range**: In `code/robustness.py`, ensure the alpha sweep for T028 covers a sufficient range (e.g., `np.logspace(start, end, 10)`) to capture the optimal regularization parameter identified in T019. Verify that the `alpha_sweep.png` plot clearly shows the minimum MAE and that the range extends beyond the optimal point to demonstrate stability. (FR-006)
- [ ] T044 [US1] [Requires: T013, T014] **Log Exclusion Reasons Explicitly**: Enhance the logging in `code/ingestion.py` (T013, T014) to include the specific numeric threshold that triggered an exclusion (e.g., `mean_fd=0.52` vs `threshold=0.5`). This ensures the exclusion logic is transparent and reproducible in `data/logs/exclusions.log`. (FR-008, FR-009)
- [X] T045 [US2] [Requires: T021, T022] **Verify Permutation Count**: Add a runtime check in `code/modeling.py` (T021) to ensure the number of permutations executed matches the configured `N=100`. If the process is interrupted or the loop terminates early, raise a `RuntimeError` to prevent reporting an invalid p-value based on insufficient permutations. (FR-005)
