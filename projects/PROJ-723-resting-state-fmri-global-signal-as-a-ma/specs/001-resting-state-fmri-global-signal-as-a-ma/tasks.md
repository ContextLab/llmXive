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
- [X] T008b [P] [Foundational] Generate `contracts/dataset.schema.yaml` defining the required columns (Subject_ID, global_signal, global_signal_sd, MWQ_Score, Age, Sex, Mean_FD, Mean_DVARS) and data types for validation. Output: `contracts/dataset.schema.yaml`. **Format**: Use JSON schema style within YAML (e.g., `type: float`, `nullable: false`). This artifact is a strict blocking dependency for downstream tasks like T010. Do not start T010 until T008b is complete. (Required by T010).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Metric Computation (Priority: P1) 🎯 MVP

**Goal**: Download HCP data, compute global signal amplitude (SD), and export a clean CSV with predictors and outcomes.

**Independent Test**: Run ingestion script on a small subset of subjects and verify output CSV contains `Subject_ID`, `Global_Signal_SD`, `MWQ_Score`, `Age`, `Sex`, `FD`, `DVARS` with no missing values.

### Implementation for User Story 1

- [X] T009 [US1] Implement data download logic in `code/ingestion.py` using the verified HCP dataset identifier `HCP-Release` or the direct URL `https://db.humanconnectome.org/data` to fetch HCP resting-state fMRI (minimally preprocessed 4D NIfTI) and MWQ scores. **Constraint**: Must stream data to avoid memory overflow; must NOT use synthetic fallbacks. **Auth**: Check for `HCP_USER` and `HCP_PASS` (or token) environment variables; if missing, raise `FileNotFoundError` with message "HCP credentials missing". If fetch fails, raise `FileNotFoundError`. **Logic**: If `datasets.load_dataset` cannot provide raw 4D NIfTI without custom auth, use a custom script to download from the verified URL or load from local cache `data/raw/hcp_cache`. Output: raw parquet files or NIfTI files in `data/raw/`. (FR-001)
- [X] T009a [US1] [Requires: T009] Implement column inspection logic in `code/ingestion.py` to verify the presence of `global_signal` or `global_signal_sd` in the fetched stream. **Critical Verification**: If missing, abort with `FATAL: Dataset Mismatch - Required columns not found in verified URL`. Output: Exit code or log entry. (FR-001)
- [X] T009b [US1] [Requires: T009a] Save the fetched raw data to `data/raw/` with checksums recorded in `state/artifact_hashes.yaml`. (FR-001)
- [X] T010 [US1] [Requires: T009b, T008b] Implement schema verification in `code/ingestion.py` using `contracts/dataset.schema.yaml`. If required columns (global_signal, global_signal_sd, etc.) are missing in the raw data, halt with `FATAL: Dataset Mismatch - Required columns not found in verified URL`. Output: Log or exit code. (FR-001)
- [X] T011 [US1] [Requires: T010] Implement voxel-wise mean time series (global signal) computation per run in `code/ingestion.py` (FR-002)
- [X] T012 [US1] [Requires: T011] Implement standard deviation calculation of global signal per run and averaging across runs per subject in `code/ingestion.py` (FR-002)
- [X] T013 [US1] [Requires: T012] [Data Hygiene] Implement subject validation logic to join fMRI and MWQ data, excluding unmatched pairs and logging counts and reasons to `data/logs/exclusions.log`. **Artifact**: `data/logs/exclusions.log` with format: `EXCLUSION: reason=pair_missing, subject_id=XXX`. (FR-009)
- [X] T014 [US1] [Requires: T013] [Data Hygiene] Implement motion exclusion logic to filter subjects where **per-subject mean FD** > 0.5mm. **Constraint**: This is a data hygiene exclusion step, NOT a model adjustment. Log exclusion counts AND subject IDs to `data/logs/exclusions.log` with format: `EXCLUSION: reason=high_motion, subject_id=XXX, mean_fd=0.XX`. Output: Filtered dataset. (FR-008)
- [X] T015 [US1] [Requires: T014] [Data Hygiene] Implement zero-variance check to exclude subjects with `global_signal_sd == 0`, raise a warning, and **log the exclusion count** to `data/logs/exclusions.log` with format: `EXCLUSION: reason=zero_variance, subject_id=XXX`. **Output**: Write a summary line `TOTAL_EXCLUDED: N=<count>` to `data/logs/exclusions.log` upon completion. (Edge Cases)
- [X] T012b [US1] [Requires: T015] [Power Analysis] Implement power analysis in `code/diagnostics.py` to calculate Minimum Detectable Effect Size (MDES) for the **actual N** (read from `data/logs/exclusions.log` by counting lines that do NOT start with "EXCLUSION"), alpha=0.05, power=0.80 using `statsmodels`. **Logic**: Wait for T015 to complete and flush logs before reading. If the actual N is insufficient to meet the power requirement (80% at alpha=0.05), **halt** the pipeline with a `FATAL: Power Insufficient` error or flag the risk in `data/logs/power_analysis.log`. **Output**: Log `data/logs/power_analysis.log` with MDES, actual N, and power risk flag. (Plan Phase 1 Step 2)
- [X] T016 [US1] [Requires: T015] Generate `data/processed/cleaned_data.csv` containing Subject_ID, Global_Signal_SD, MWQ_Score, Age, Sex, Mean_FD, Mean_DVARS
- [X] T017 [P] [US1] Unit test: Verify global signal SD calculation matches manual calculation on sample data in `tests/test_ingestion.py`
- [X] T018 [P] [US1] Unit test: Verify exclusion logic for missing pairs and high motion subjects in `tests/test_ingestion.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Association Modeling and Baseline Comparison (Priority: P2)

**Goal**: Run ridge regression to predict MWQ from global signal amplitude (adjusted for covariates), compare against null model, and generate report.

**Independent Test**: Run modeling script on synthetic data (r=0.3) and verify out-of-fold Pearson r falls within 0.25–0.35 and null model performance is near zero.

### Implementation for User Story 2

- [X] T019 [US2] Implement primary ridge regression pipeline in `code/modeling.py` with nested k-fold CV for alpha tuning (FR-004). **Output**: Persist results to `data/results/full_model.json` (containing MAE, r, R², alpha) AND save residuals to `data/processed/residuals.csv` (containing Subject_ID, residual_value). (FR-004)
- [X] T019a [US2] [Requires: T019] **Verify** the primary model structure in `code/modeling.py` explicitly includes `FD` and `DVARS` as predictors in the formula `Y ~ Global_Signal_SD + FD + DVARS + Age + Sex`. **Logic**: Parse the model definition string or inspect the feature matrix columns used in the Ridge estimator. **Output**: Log `data/logs/model_structure_check.log` with `STATUS: PASS` or `STATUS: FAIL`. If FAIL, halt execution. (FR-003, FR-004)
- [X] T020 [US2] [Requires: T019] Implement model structure `Y ~ Global_Signal_SD + FD + DVARS + Age + Sex` in `code/modeling.py` (FR-003, FR-004)
- [X] T021 [US2] [Requires: T019, T016] **Execute** the null distribution generation in `code/modeling.py` by **independently permuting the MWQ score vector** (using `seed=42` for reproducibility) and running the full nested CV pipeline for each permutation. **Logic**: Start with N=100. Continue permutations until the standard deviation of the null MAE distribution is < 0.001 OR N reaches a sufficient sample size for statistical power.. **Write** the resulting MAE and R² values to `data/results/null_distribution.json`. **Constraint**: If the process is interrupted, write partial results to `data/results/null_distribution_partial.json` to prevent data loss. **Constraint**: Calculate empirical p-value using the formula $p = \frac{\text{count}(\text{Null MAE} \le \text{Observed MAE}) + 1}{N + 1}$. **Verification**: Verify that the calculated p-value is reported with appropriate decimal precision and that the null distribution histogram is saved to `data/results/null_dist.png`. (FR-005, Plan Constraint)
- [X] T022 [US2] [Requires: T021, T019] Implement empirical p-value calculation: read `data/results/null_distribution.json` and the observed MAE from `data/results/full_model.json` (T019's execution output), then calculate the proportion of null MAEs <= observed MAE (standard convention, SC-002). (FR-005)
- [X] T023 [US2] [Requires: T019, T016] Implement Reduced Model (Y ~ FD + DVARS + Age + Sex) to isolate GSA effect. **Logic**: Read the Full Model results (R²) from `data/results/full_model.json` (T019's execution output). Calculate Delta R² (Full R² - Reduced R²). **Fallback**: If Reduced Model fails (e.g., collinearity), output `data/results/delta_r2.json` with schema `{'status': 'failed', 'reason': 'High Collinearity', 'delta_r2': null}` and log 'High Collinearity' and set a flag to trigger narrative change in T025. Output: `data/results/delta_r2.json` containing Delta R² and status. (Plan Methodology)
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
- [X] T030 [US3] [Requires: T016, T019] Implement partial correlation analysis controlling for mean FD to verify independence of GSA effect. **Logic**: Use the **residuals from the FULL Ridge Regression model (Y ~ GSA + FD + DVARS + Age + Sex)** saved in `data/processed/residuals.csv` (T019 output) to calculate partial correlation. **Note**: This is a supplementary robustness check, not the primary verification of FR-003 (which is handled by T019a). **Verification**: Calculate and report the p-value. **Output**: Write results to `data/results/partial_corr.json` with keys `p_value`, `status` (values: 'significant' if p < 0.05, else 'null_finding'), and `method`. **Comparison**: Compare the p-value against the SC-005 baseline (p < 0.05) and report the 'independence status' (met/not met). Do NOT assert p < 0.05; report the actual result and status. (FR-003, SC-005)
- [X] T031 [US3] [Requires: T028, T029, T030] Generate `data/results/robustness_report.json` containing alpha sweep results, variance metric correlation, and partial correlation stats
- [X] T032 [P] [US3] Unit test: Verify alpha sweep results match expected MAE variations in `tests/test_robustness.py`
- [X] T033 [P] [US3] Unit test: Verify variance metric correlation is within ±0.05 of primary SD result in `tests/test_robustness.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Final Validation

**Purpose**: Aggregate results and verify success criteria.

- [X] T034a [P] [US3] Aggregate all results into `data/results/final_report.json` (Primary, Null, Robustness). (SC-001 to SC-005)
- [ ] T034b [P] [Requires: T034a] **Regenerate** `final_report.json` with `criteria_status` object. **Logic**: Read p-value, correlation, and stability metrics from the aggregated `data/results/final_report.json` (T034a output). **Schema**: Write a JSON object `criteria_status` with keys `SC-001` through `SC-005`. Each entry must contain: `status` (met/not met), `narrative_summary` (string), AND `metrics` (object containing the specific empirical values: `p_value`, `correlation_coefficient`, `mae`, `r_squared` as applicable). **Constraint**: If p-value >= 0.05, explicitly state the null finding in a `narrative_summary` field. Do NOT assert significance; report the actual status. **Thresholds**: SC-001/002: p < 0.05; SC-003: |r_var - r_sd| <= 0.05; SC-004: MAE variation < 10%; SC-005: p < 0.05. **Output**: Add `criteria_status` object with `metrics` and `narrative_summary` string for each SC describing the outcome (e.g., "Significant: p=0.03" or "Null Finding: p=0.12, no evidence of association"). (SC-001 to SC-005)
- [X] T035 [P] [Requires: T034a] Generate visualizations: `data/results/null_dist.png`, `data/results/alpha_sweep.png`, `data/results/corr_matrix.png` using `matplotlib`. **Validation**: Verify all files exist and have non-zero size. (SC-001 to SC-005)
- [X] T036a [P] [Requires: T016] **Generate** a small synthetic test fixture (`data/tests/test_fixture.csv`) with N=10 subjects containing valid columns (Subject_ID, Global_Signal_SD, MWQ_Score, Age, Sex, Mean_FD, Mean_DVARS). **Constraint**: This fixture is for integration testing ONLY and must NOT be used in the real analysis pipeline (T009 forbids synthetic fallbacks). (Test Requirement)
- [ ] T036 [P] [Requires: T034a, T036a] Run end-to-end integration test on full pipeline using the **test fixture** from T036a. **Validation**: Verify the test passes and logs are generated. (SC-001 to SC-005)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (requires `cleaned_data.csv` from US1)
- **User Story 3 (P3)**: Depends on US1 (requires `cleaned_data.csv`) and modeling logic (T019), but can run in parallel with US2 reporting (T025).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- US3 (T028, T029, T030) can run in parallel with US2 reporting (T025) once T016 and T019 are complete.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must be feasible on CPU-only CI with limited computational resources, including a small number of cores, approximately modest RAM, and no GPU. No 8-bit/4-bit quantization, no large LLMs, no deep nets from scratch.
- **Data Integrity Rule**: If a verified real data source is injected, USE it. Do not fall back to synthetic data. If data fetch fails, the script must fail loudly.