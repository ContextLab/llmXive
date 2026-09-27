# Tasks: The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

**Input**: Design documents from `/specs/001-simulated-social-comparison-self-esteem/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

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

- [X] T001a [P] Initialize project structure: Create root directory `projects/PROJ-490-the-effect-of-simulated-social-compariso/` and subdirectories `code/`, `data/`, `tests/`, `docs/`, `state/`, `data/raw`, `data/processed`, `tests/contract`, `tests/unit`.
- [X] T001b [P] Configure linting (flake8/pylint) and formatting (black) tools, and create `requirements.txt`, `README.md`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002a [P] Create `dataset.schema.yaml` in `projects/PROJ-490-the-effect-of-simulated-social-compariso/contracts/`. **Explicit Definitions**:
 ```yaml
 type: object
 required:
 - participant_id
 - pre_self_esteem
 - post_self_esteem
 - comparison_tendency
 - avatar_condition
 properties:
 participant_id:
 type: string
 description: Unique identifier
 pre_self_esteem:
 type: number
 description: RSES score, pre-intervention
 post_self_esteem:
 type: number
 description: RSES score, post-intervention
 comparison_tendency:
 type: number
 description: INCOM scale score
 avatar_condition:
 type: integer
 enum: [0, 1]
 description: 0=Neutral, 1=Idealized
 ```
 Include validation rules for N ≥ 100 participants (FR-001).
- [X] T002b [P] Create `output.schema.yaml` in `projects/PROJ-490-the-effect-of-simulated-social-compariso/contracts/`. **Explicit Definitions**:
 ```yaml
 type: object
 required:
 - imputed_data_checksum
 - missingness_report
 properties:
 imputed_data_checksum:
 type: string
 missingness_report:
 type: object
 properties:
 total_rows:
 type: integer
 rows_excluded:
 type: integer
 missingness_pct:
 type: number
 ```
- [X] T002c [P] Create `results.schema.yaml` in `projects/PROJ-490-the-effect-of-simulated-social-compariso/contracts/`. **Explicit Definitions**:
 ```yaml
 type: object
 required:
 - coefficients
 - assumptions
 - data_source_type
 properties:
 coefficients:
 type: array
 items:
 type: object
 properties:
 name:
 type: string
 estimate:
 type: number
 std_err:
 type: number
 p_value:
 type: number
 assumptions:
 type: object
 properties:
 shapiro_p:
 type: number
 breusch_pagan_p:
 type: number
 vif_max:
 type: number
 data_source_type:
 type: string
 enum: ["real", "synthetic"]
 ```
- [X] T003 [P] Implement schema validation utilities in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/utils/validators.py`. **CRITICAL**: Define `DataFetchError` exception class here for use in data fetching tasks.
- [X] T004 [P] Setup logging infrastructure in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/utils/logger.py`
- [X] T005 [P] Create configuration manager for seeds and paths in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Discovery and Validation (Priority: P1) 🎯 MVP

**Goal**: Locate valid real-world datasets (RSES, INCOM, pre/post) or initialize synthetic data generator with ground truth.

**Independent Test**: Can be fully tested by successfully querying HuggingFace Datasets, OpenML, and Open Science Framework repositories and documenting either: (a) at least one real dataset with N ≥ 100 participants containing RSES, INCOM, and pre/post scores, OR (b) a successful initialization of the synthetic data generator with defined ground-truth parameters.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T006 [P] [US1] Contract test for dataset schema validation in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/contract/test_dataset_schema.py`
- [X] T007 [P] [US1] Unit test for synthetic data generator parameter recovery in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/unit/test_synthetic_gen.py`

### Implementation for User Story 1

- [X] T008 [P] [US1] Implement dataset discovery script in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` to query HuggingFace, OpenML, and OSF for RSES/INCOM/PrePost variables. **CRITICAL**: Raise `DataFetchError` (defined in T003) on network failures.
- [X] T009a [US1] **IRB/Consent Verification Logic** (DEPENDS ON T008 output): Implement logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` to verify consent documentation.
 1. Check for existence of IRB/Consent artifact in `data/raw/consent_forms/`.
 2. **File Format**: Accept `.pdf` or `.txt` files only.
 3. **Verification**: Scan file content for keywords 'IRB' or 'Consent'.
 4. **Return a structured validation object** (JSON schema):
    ```json
    {
      "valid": boolean,
      "reason": "string (e.g., 'File not found', 'Missing keywords')",
      "source": "string (dataset_id or null)"
    }
    ```
 5. Log specific findings (file path, keywords found) to `logs/irb_check.log`. **Do NOT log the full content of the consent form.**
 **Artifact**: No standalone file; returns a validation object for downstream tasks.
 **Note**: This task is strictly for verification. It does NOT trigger fallbacks or update state.
- [X] T009b [US1] **Fallback Trigger and State Update** (DEPENDS ON T009a): Implement logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` to handle the decision.
 1. Consume the validation object from T009a.
 2. **Logic**:
    - If `valid` is False AND real data exists: **HALT** execution and flag the data as unusable (do NOT generate synthetic data to replace valid real data).
    - If no real data is found by T008: Trigger synthetic generation (T010).
 3. Update `state/data_path_decision.yaml` with the decision and reason.
 4. Generate `data/raw/synthetic_seed.json` if synthetic generation is triggered.
 **Artifact**: `state/data_path_decision.yaml` containing:
 ```yaml
 decision: real | synthetic
 reason: <string>
 timestamp: <ISO8601>
 source: <dataset_id or null>
 ```
 (Constitution Principle VI, FR-011, FR-014).
- [X] T010 [P] [US1] Implement synthetic data generator in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` with N ≥ 100, interaction β = 0.2, and "Pipeline Validation Only" labeling (FR-011). **Ground Truth Parameters**: intercept=0, main_effect_avatar=0.1, main_effect_comparison=0.1, interaction_beta=0.2, noise_sigma=1.0. All values must be hardcoded or loaded from a config file to ensure reproducibility.
- [X] T012 [P] [US1] Create `data/raw` loader that saves downloaded CSVs or synthetic outputs and writes checksums to `state/projects/PROJ-490-the-effect-of-simulated-social-compariso.yaml` (Constitution Principle III, V).
- [X] T013a [US1] **Sample Size Enforcement and Pre-Imputation Variable Check** (DEPENDS ON T012, T009b): Verify `data/raw` contains ALL required variables (avatar_condition, pre_self_esteem, post_self_esteem, comparison_tendency) BEFORE imputation. If any are missing, trigger T010 (Synthetic). Write validation status to `data/processed/pre_imputation_validation.json`. **Action: Explicitly write data/processed/pre_imputation_validation.json with validation status.**
 **Artifact Schema**:
 ```json
 {
 "status": "pass" | "fail",
 "missing_vars": [],
 "timestamp": "ISO8601"
 }
 ```
 (FR-009).
- [X] T014a [US2] **Sample Size Enforcement (Defensive Check)** (DEPENDS ON T013a): Implement logic in `code/data/preprocess.py` to check N ≥ 100 (FR-001). If N < 100, raise `ValueError` with message "Sample size < 100". **Note**: This is a defensive check; T013a should have already passed. If T013a failed, this task should not run.
- [X] T014b [US2] **MICE Exclusion Logic** (DEPENDS ON T013a): Implement logic in `code/data/preprocess.py` to count missingness per row. If a row has > 20% missingness across key variables, exclude it from imputation (FR-002). Log excluded row IDs.
- [X] T016 [US2] **Implement Missing Data Handling and Save** (DEPENDS ON T012, T013a, T014a, T014b): Implement logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/preprocess.py` using `miceforest` (primary) for < 20% missingness; fallback to `sklearn.impute.IterativeImputer` if `miceforest` unavailable; exclude rows with > 20% (FR-002, FR-013).
 1. Perform imputation in memory.
 2. **CRITICAL OUTPUT**: Explicitly save the resulting imputed DataFrame to `data/processed/imputed_data.csv` immediately after processing.
 3. Include explicit try/except block to detect `miceforest` unavailability and switch to `sklearn.impute.IterativeImputer`, logging the switch event.
 **Artifact**: `data/processed/imputed_data.csv` (FR-013). **Success Condition**: File exists and is non-empty.
 **Note**: This task includes the logic previously in T016a (Write Imputed Data) to ensure atomicity.
- [X] T013b [US1] **Post-Imputation Validation** (DEPENDS ON T016): Verify `data/processed/imputed_data.csv` contains clean data after T016. Write validation status to `data/processed/post_imputation_validation.json`. **Action: Explicitly write data/processed/post_imputation_validation.json.** **Success Condition**: File exists, is non-empty, and row count matches expected input (minus excluded rows).
 **Artifact Schema**:
 ```json
 {
 "status": "pass" | "fail",
 "imputation_success": true | false,
 "timestamp": "ISO8601"
 }
 ```
- [X] T017 [US2] Implement variable normalization (avatar_condition to 0/1 if binary) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/preprocess.py` AND compute change scores (post_self_esteem - pre_self_esteem) **strictly for in-memory logging/diagnostics ONLY**. **CRITICAL**: Do NOT use change scores as the outcome. The primary model must use ANCOVA (outcome: post_self_esteem, covariate: pre_self_esteem) to avoid mathematical coupling as mandated by the Plan. **DO NOT persist change scores to disk**. Log a warning in `logs/preprocess.log` that these are for descriptive use only. **DEPENDS ON T013a, T016**. **Note**: This task is non-blocking; if change score calculation fails, log a warning and proceed. Downstream tasks (T013b, T022) depend on the *imputed dataset* (from T016), not the change score.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (data path selected and validated).

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline (Priority: P2)

**Goal**: Preprocess data (MICE), fit ANCOVA regression, and validate model assumptions.

**Independent Test**: Can be fully tested by running the complete analysis pipeline on a sample dataset (real or synthetic) and producing reproducible output artifacts (a CSV file containing regression coefficients and a JSON file containing diagnostic metrics) within ≤6 hours on CPU-only hardware.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T014 [P] [US2] Contract test for regression output schema in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/contract/test_results_schema.py`
- [X] T015 [P] [US2] Unit test for MICE imputation on missing < 20% vs > 20% exclusion logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/unit/test_preprocess.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement ANCOVA regression model in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/regression.py` (outcome: post_self_esteem, covariate: pre_self_esteem, predictors: avatar_condition, comparison_tendency, interaction). Explicitly document in code comments that this implements the ANCOVA approach (avoiding mathematical coupling) as mandated by the Plan. **DEPENDS ON T013a, T016**.
- [X] T018a [US2] **ANCOVA Constraint Verification** (DEPENDS ON T018): Add unit test in `tests/unit/test_preprocess.py` to assert that `post_self_esteem` is the outcome and `pre_self_esteem` is the covariate in the model formula. Ensure no change scores are used as the outcome variable.
- [X] T019 [US2] Implement assumption validation in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/regression.py`: Shapiro-Wilk (normality), Breusch-Pagan (homoscedasticity), VIF (collinearity) (FR-004).
- [X] T021 [US2] Export regression coefficients to `data/processed/regression_coefficients.csv` and diagnostics to `data/processed/model_diagnostics.json` (FR-008). **Action: Explicitly write regression_coefficients.csv and model_diagnostics.json to disk.** **DEPENDS ON T018, T019**.
- [X] T022 [US2] Handle collinearity (VIF ≥ 5) by flagging and framing results descriptively without claiming independent effects. Update `data/processed/model_diagnostics.json` with `collinearity_warning` key (Assumptions). **DEPENDS ON T019, T021**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (data loaded, model fitted, assumptions checked).

---

## Phase 5: User Story 3 - Methodological Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Conduct bootstrap resampling with a sufficient number of iterations to ensure robust estimation. and sensitivity sweeps to validate stability.

**Independent Test**: Can be fully tested by executing bootstrap resampling and threshold sensitivity sweeps on the fitted model and documenting how parameter recovery error (for synthetic data) or significance stability (for real data) varies across different cutoff values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for bootstrap stability calculation (CI width variance < 0.01) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/unit/test_bootstrap.py`
- [X] T024 [P] [US3] Unit test for parameter recovery bias calculation (|beta_hat - beta_true|) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [X] T025 [US3] Implement bootstrap resampling in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/bootstrap.py` with **at least 1,000 iterations OR until CI width variance < 0.01 is achieved (FR-005), whichever comes first**. **CRITICAL**: Set `max_iterations=1000`. If variance < 0.01 is not achieved after max iterations, log a warning, record the final variance, and proceed with the best available CI. Do NOT fail. Record the instability in the final report. **DEPENDS ON T018**.
- [X] T028a [US3] **Implement Threshold Sensitivity Sweep Logic** (DEPENDS ON T013a, T021): Implement logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` for p-value thresholds (conventional significance levels) and imputation limits.
 1. **Threshold List**: Generate a list of thresholds `[0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20]`.
 2. Include the complete case baseline.
 3. **Output**: Return an in-memory result object containing the sweep results (threshold, bias, variance, baseline_id).
 4. **Artifact**: Write the list of thresholds and baseline logic to `data/processed/sensitivity_thresholds.json` for T028b consumption.
 5. Log the sweep range and parameters to `logs/sensitivity.log`.
 **Note**: This task strictly handles the logic and calculation. It does NOT write the final CSV.
 **DEPENDS ON T013a, T021**.
- [X] T028b [US3] **Implement Sensitivity Sweep Artifact Generation** (DEPENDS ON T028a): Implement logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` to write the results from T028a to disk.
 1. **Action**: Explicitly write `data/processed/sensitivity_sweep_results.csv` containing columns `[threshold, bias, variance, baseline_id]`.
 2. Ensure the file is written only after T028a completes successfully.
 **DEPENDS ON T028a**.
- [X] T027 [US3] Implement parameter recovery analysis in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` for synthetic data: compare estimated coefficients to ground truth (FR-011, SC-005). **DEPENDS ON T028b**.
- [X] T029 [US3] Apply family-wise error correction (Bonferroni/Holm) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` (FR-006): Apply correction **only** to the set of tests generated by sensitivity sweeps (thresholds + imputation limits). **Explicitly EXCLUDE model assumption tests (Shapiro, Breusch-Pagan, VIF) AND the primary interaction hypothesis test** as these are diagnostic checks or pre-registered hypotheses, not part of the sweep family. **DEPENDS ON T028b**.
- [X] T029a [US3] **Primary Interaction Error Correction** (DEPENDS ON T029): Implement explicit Bonferroni/Holm correction logic for the **primary interaction hypothesis test** (avatar_condition * comparison_tendency) in `code/analysis/sensitivity.py`. Ensure the corrected p-value is recorded in the final report. **Note**: This is a separate correction step, not part of the sweep family correction in T029.
- [X] T030 [US3] Generate final report JSON containing: data path used, model results, bootstrap stability, parameter recovery (if synthetic), and sensitivity findings (FR-012). Write to `data/processed/final_report.json`.
 **Artifact Schema**:
 ```json
 {
 "data_source_type": "real" | "synthetic",
 "model_coefficients": [],
 "bootstrap_ci_variance": 0.0,
 "parameter_recovery_bias": 0.0,
 "sensitivity_results": [],
 "stability_failed": false,
 "interpretation": "Empirical Association" | "Simulated Causal Effect"
 }
 ```
 **DEPENDS ON T025, T027, T028b, T029, T029a**.
- [X] T030a [US3] **Interpretation Labeling Logic** (DEPENDS ON T030): Implement logic to set the `interpretation` field based on `data_source_type`. If `real`, set to "Empirical Association". If `synthetic`, set to "Simulated Causal Effect". (FR-010).

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Documentation updates in `docs/analysis_plan.md` and `README.md`
- [X] T032a [P] Run `flake8` on `code/` and fix all errors (zero errors remaining)
- [X] T032b [P] Run `black` on `code/` and `tests/` and fix all formatting violations. **DEPENDS ON T032a**.
- [X] T033 [P] Run `pytest` on all unit and contract tests in `tests/`
- [X] T034 [P] Verify reproducibility by running `main.py` twice with fixed seeds and comparing output hashes. Writes the hash comparison results to `state/reproducibility_check.yaml` (Constitution Principle III, V). **DEPENDS ON T052**.
- [X] T035 [P] Run quickstart.md validation if available

---

## Phase 7: Execution Feasibility (Streamlined)

**Purpose**: Ensure the pipeline runs successfully on the free CPU runner with dynamic resource checks.

- [X] T050 [US1] **CRITICAL**: Implement dynamic resource checking in `code/data/download.py`. Use `psutil` or `os.sysconf` to estimate available RAM. If estimated dataset size exceeds a significant proportion of available RAM, implement chunked processing or trigger a warning with explicit logging of the sampling strategy. **NO hardcoded thresholds**. (FR-001, Plan constraints).
- [X] T051 [US3] **CRITICAL**: Implement dynamic memory estimation in `code/analysis/bootstrap.py`. Before starting bootstrap, estimate memory usage. If estimated usage exceeds 80% of available RAM, reduce iterations to a minimum of 100 and log the reduction. Record the actual number of iterations and the reason for reduction in `final_report.json`. (FR-005, Plan constraints).

**Checkpoint**: Pipeline is safe for execution on free CPU runner.

---

## Phase 8: Main Entry Point & Integration

**Purpose**: Create the central orchestrator that ties all components together and ensures the quickstart command works.

- [X] T052 [P] **Main Entry Point Implementation**: Create `code/main.py` in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/`. This script must:
 1. Import and execute the data discovery pipeline (T008, T009a, T009b).
 2. Trigger data loading/synthetic generation (T010, T012).
 3. Run preprocessing (T013a, T014a, T014b, T016, T017).
 4. Execute the ANCOVA model (T018, T019, T021, T022).
 5. Run robustness checks (T025, T028a, T027, T029, T029a).
 6. Generate the final report (T030, T030a).
 7. Handle all logging and error states as defined in `code/utils/logger.py`.
 **DEPENDS ON**: All implementation tasks in Phases 1-7.
 **Artifact**: `code/main.py` executable script.

---

## Phase 9: Execution Safety & Data Integrity (Revision)

**Purpose**: Address critical review concerns regarding data loading, synthetic fallbacks, and execution safety. These tasks ensure the pipeline never fabricates data and handles real data correctly.

- [ ] T053 [P] [US1] **Enforce Strict Real Data Fetching with Fallback**: Modify `code/data/download.py` (T008) to handle fetch failures gracefully. If a real fetch fails OR IRB consent is missing (and no valid real data exists), the script MUST trigger synthetic generation (T010) and log the specific reason (e.g., "Fetch failed", "No consent"). **Do NOT halt execution** unless real data exists but lacks consent (in which case, see T009b). (FR-009, Constitution Principle III).
- [ ] T054 [P] [US1] **Implement Verified Real Data Source Injection**: Modify `code/data/download.py` to check for a `VERIFIED_REAL_DATA_SOURCE` environment variable or config flag. **Expected Format**: A HuggingFace dataset ID (e.g., "org/dataset") or a local file path. If present, the loader MUST use the specified package/recipe exactly, **BUT MUST STILL RUN T009a (IRB Check)** before proceeding to ensure constitutional compliance. (FR-009, Constitution Principle III).
- [ ] T055 [P] [US1] **Add Explicit Synthetic Data Labeling**: Ensure `code/data/download.py` (T010) explicitly writes a `data_source_type` field to the output CSV and JSON artifacts, setting it to "synthetic" with a comment "Pipeline Validation Only". (FR-011).
- [ ] T056 [P] [US2] **Add Streaming Support for Large Datasets**: Modify `code/data/preprocess.py` (T016) to support streaming large datasets using `datasets.load_dataset(..., streaming=True)` if the dataset size exceeds **[deferred] of available RAM**. Process data in chunks (e.g., a fixed batch size) and accumulate statistics online. (FR-001, Plan constraints).
- [ ] T057 [P] [US3] **Add Bootstrap Memory Safety**: Modify `code/analysis/bootstrap.py` (T025) to include a hard limit on memory usage (e.g., 7 GB) and dynamically adjust the number of bootstrap iterations if the limit is approached. Log the adjustment and record the actual number of iterations performed. (FR-005, Plan constraints).
- [ ] T058 [P] [US1] **Add Data Integrity Checksums**: Modify `code/data/download.py` (T012) to compute and store SHA-256 checksums for all downloaded real datasets and synthetic data files. Verify these checksums before processing. (Constitution Principle III).
- [ ] T059 [P] [US1] **Add IRB Consent Artifact Logging**: Modify `code/data/download.py` (T009a) to log the exact **path** of any IRB/Consent artifacts found, ensuring transparency in the verification process. **Do NOT log the content** of the consent forms to preserve Data Hygiene and Ethical Human Subjects principles. (FR-009, Constitution Principle VI).
- [ ] T060 [P] [US2] **Add MICE Imputation Fallback Logging**: Modify `code/data/preprocess.py` (T016) to log a detailed message if `miceforest` is unavailable and `sklearn.impute.IterativeImputer` is used, including the reason for the fallback. (FR-013).
- [ ] T061 [P] [US3] **Add Sensitivity Sweep Range Validation**: Modify `code/analysis/sensitivity.py` (T028a) to validate that the sensitivity sweep range (imputation limits, p-value thresholds) is within reasonable bounds (e.g., 0.0 to 0.20 for imputation limits) and log any adjustments made. (FR-007).
- [ ] T062 [P] [US3] **Add Final Report Interpretation Validation**: Modify `code/analysis/sensitivity.py` (T030) to validate that the `interpretation` field in the final report matches the `data_source_type` (e.g., "Empirical Association" for real, "Simulated Causal Effect" for synthetic). (FR-010).