# Tasks: The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

**Input**: Design documents from `/specs/001-simulated-social-comparison-self-esteem/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
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

**Checkpoint**: Foundation ready - user story implementation can begin in parallel

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
 1. **Mapping Logic**: Extract the dataset ID from the remote source URL/metadata (e.g., using `huggingface_hub` API or URL parsing) and map it to a local file path: `data/raw/consent_forms/{dataset_id}.pdf` or `data/raw/consent_forms/{dataset_id}.txt`.
 2. Check for existence of IRB/Consent artifact at the mapped path.
 3. **File Format**: Accept `.pdf` or `.txt` files only.
 4. **Verification**: Scan file content for keywords 'IRB' or 'Consent' using PyPDF2 for PDFs.
 5. **Return a structured validation object** (JSON schema):
 ```json
 {
 "valid": boolean,
 "reason": "string (e.g., 'File not found', 'Missing keywords', 'Scan failed')",
 "source": "string (dataset_id or null)"
 }
 ```
 6. **Fallback Behavior**: If IRB file is missing or scan fails, return `valid: false` with the specific reason. Do NOT silently fallback. This object is consumed by T009b/T063 to trigger synthetic fallback.
 7. Log specific findings (file path, keywords found) to `logs/irb_check.log`. **Do NOT log the full content of the consent form.**
 **Artifact**: No standalone file; returns a validation object for downstream tasks.
 **Note**: This task is strictly for verification. It does NOT trigger fallbacks or update state.
- [X] T009b [US1] **Fallback Trigger and State Update** (DEPENDS ON T009a): Implement logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` to handle the decision.
 1. Consume the validation object from T009a.
 2. **Logic**:
 - If `valid` is False AND real data exists: **Trigger synthetic generation** (T010) and flag the real data as unusable. Do NOT halt execution.
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
- [X] T010 [P] [US1] Implement synthetic data generator in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` with N ≥ 100, interaction β = 0.2, and "Pipeline Validation Only" labeling (FR-011). **Ground Truth Parameters**: intercept=0, main_effect_avatar=0.1, main_effect_comparison=0.1, interaction_beta=0.2, noise_sigma=1.0. **Distribution**: Multivariate Normal. **Correlation Structure**: 0.6 between `pre_self_esteem` and `post_self_esteem`, 0.3 between `comparison_tendency` and `avatar_condition`. All values must be hardcoded or loaded from a config file to ensure reproducibility.
- [X] T012 [P] [US1] Create `data/raw` loader that saves downloaded CSVs or synthetic outputs and writes checksums to `state/projects/PROJ-490-the-effect-of-simulated-social-compariso.yaml` (Constitution Principle III, V).
- [X] T013a [US1] **Sample Size Enforcement and Pre-Imputation Variable Check** (DEPENDS ON T012, T009b): Verify `data/raw` contains ALL required variables (avatar_condition, pre_self_esteem, post_self_esteem, comparison_tendency) BEFORE imputation.
 1. **Action**: Explicitly write `data/processed/pre_imputation_validation.json` with validation status.
 2. **Artifact Schema**:
 ```json
 {
 "status": "pass" | "fail",
 "missing_vars": [],
 "timestamp": "ISO8601"
 }
 ```
 3. **Fallback Logic**: If any required variables are missing, **immediately trigger synthetic generation** (T010), write `status: "fail"` to the artifact, and halt the real-data path. Do NOT proceed to T014a.
 4. **Dependency Check**: T014a/T014b must verify this artifact exists before proceeding.
 (FR-009).
- [X] T014a_new [US1] **Original Sample Size Enforcement** (DEPENDS ON T013a): Verify the *original* dataset size (before any sampling) meets N ≥ 100 (FR-001).
 1. **Logic**: If original N < 100, **HALT** execution immediately. Do NOT proceed to sampling or imputation. Write `status: "fail"` to `data/processed/pre_imputation_validation.json` with reason "Original N < 100".
 2. **Rationale**: Sampling cannot increase N. This check prevents running on a sample of a small dataset.
 3. **Action**: Write `status: "fail"` and halt.
 (FR-001).
- [X] T014b [US2] **MICE Exclusion Logic** (DEPENDS ON T013a, T014a_new): Implement logic in `code/data/preprocess.py` to count missingness per row.
 1. **Dependency Check**: Verify `data/processed/pre_imputation_validation.json` exists and has `status: "pass"`. If missing or `status: "fail"`, raise `ValueError`.
 2. If a row has > 20% missingness across key variables, exclude it from imputation (FR-002). Log excluded row IDs.
- [X] T016 [US2] **Implement Missing Data Handling and Save** (DEPENDS ON T012, T013a, T014a_new, T014b): Implement logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/preprocess.py` using `miceforest` (primary) for < 20% missingness; fallback to `sklearn.impute.IterativeImputer` if `miceforest` unavailable; exclude rows with > 20% (FR-002, FR-013).
 1. Perform imputation in memory.
 2. **CRITICAL OUTPUT**: Explicitly save the resulting imputed DataFrame to `data/processed/imputed_data.csv` immediately after processing.
 3. Include explicit try/except block to detect `miceforest` unavailability and switch to `sklearn.impute.IterativeImputer`, logging the switch event.
 **Artifact**: `data/processed/imputed_data.csv` (FR-013). **Success Condition**: File exists and is non-empty.
 **Note**: This task includes the logic previously in T016a (Write Imputed Data) to ensure atomicity.
- [X] T013b [US1] **Post-Imputation Validation** (DEPENDS ON T016): Verify `data/processed/imputed_data.csv` contains clean data after T016.
 1. **Action**: Explicitly write `data/processed/post_imputation_validation.json`.
 2. **Artifact Schema**:
 ```json
 {
 "status": "pass" | "fail",
 "imputation_success": true | false,
 "timestamp": "ISO8601"
 }
 ```
 3. **Fallback Logic**: If T016 fails or produces an empty file, write `status: "fail"` to the artifact and trigger synthetic generation (T010).
 4. **Success Condition**: File exists, is non-empty, and row count matches expected input (minus excluded rows).
- [X] T017 [US2] **Compute Descriptive Change Scores** (DEPENDS ON T013b, T016): Compute `post_self_esteem - pre_self_esteem` for logging/diagnostics ONLY.
 1. **Logic**: If `data/processed/imputed_data.csv` exists, compute change scores. If not, skip and log "Imputation data missing, skipping descriptive change score calculation".
 2. **CRITICAL**: Do NOT use change scores as the outcome. The primary model must use ANCOVA (outcome: post_self_esteem, covariate: pre_self_esteem) to avoid mathematical coupling as mandated by the Plan.
 3. **Output**: Write a `diagnostics/change_score_status.json` file with keys `status` (success/skipped) and `message`.
 4. Log a warning in `logs/preprocess.log` that these are for descriptive use only.
 **Note**: This task is non-blocking; if change score calculation fails, log a warning and proceed. Downstream tasks (T013b, T022) depend on the *imputed dataset* (from T016), not the change score.

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
- [X] T018a [US2] **ANCOVA Constraint Verification** (DEPENDS ON T018): Add unit test in `tests/unit/test_regression.py` to assert that `post_self_esteem` is the outcome and `pre_self_esteem` is the covariate in the model formula. Ensure no change scores are used as the outcome variable.
- [X] T019 [US2] Implement assumption validation in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/regression.py`: Shapiro-Wilk (normality), Breusch-Pagan (homoscedasticity), VIF (collinearity) (FR-004).
- [X] T021 [US2] Export regression coefficients to `data/processed/regression_coefficients.csv` and diagnostics to `data/processed/model_diagnostics.json` (FR-008). **Action: Explicitly write regression_coefficients.csv and model_diagnostics.json to disk.** **DEPENDS ON T018, T019**.
- [X] T022 [US2] Handle collinearity (VIF ≥ 5) by flagging and framing results descriptively without claiming independent effects. Update `data/processed/model_diagnostics.json` with `collinearity_warning` key (Assumptions). **DEPENDS ON T019, T021**.
- [X] T076b [US2] **Enforce CPU-Only Execution Constraint** (DEPENDS ON T018): Modify `code/analysis/regression.py` to explicitly detect and reject any attempt to use GPU acceleration (CUDA).
 1. **Logic**: Check for `torch.cuda.is_available()` or `tensorflow.config.list_physical_devices('GPU')`. If true, log a warning and force CPU device usage (`device="cpu"`).
 2. **Rationale**: The project constraints mandate CPU-only execution on the free runner. Any GPU dependency must be neutralized to prevent execution failure.
 3. **Action**: Ensure all statistical operations (MICE, ANCOVA, Bootstrap) run on CPU tensors/dataframes.
 4. **Artifact**: Update `logs/execution_mode.log` with "CPU-Only Mode Enforced".
 (Plan Constraints, FR-001).
- [X] T077_new [US2] **Implement Memory-Efficient MICE for Large Samples** (DEPENDS ON T064, T066): Refine `code/data/preprocess.py` to handle datasets approaching the 7GB RAM limit without swapping.
 1. **Strategy**: If the dataset size (after streaming/sampling) is > 4GB, **DO NOT** attempt 'chunked MICE' (statistically invalid). Instead, **extract a stratified random sample** (N >= 100, preserving correlation structure via seed) and run standard MICE on that sample.
 2. **Constraint**: Do NOT attempt to load the full dataset if it exceeds 6GB.
 3. **Logging**: Log the final dataset size used for imputation, the sample size, and the memory footprint estimate. Explicitly log that 'chunked MICE' was avoided.
 (FR-002, Plan Constraints).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (data loaded, model fitted, assumptions checked).

---

## Phase 5: User Story 3 - Methodological Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Conduct bootstrap resampling with a sufficient number of iterations to ensure robust estimation. and sensitivity sweeps to validate stability.

**Independent Test**: Can be fully tested by executing bootstrap resampling and threshold sensitivity sweeps on the fitted model and documenting how parameter recovery error (for synthetic data) or significance stability (for real data) varies across different cutoff values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for bootstrap stability calculation (CI width variance < 0.01) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/unit/test_bootstrap.py`
- [X] T024 [P] [US3] Unit test for parameter recovery bias calculation (|beta_hat - beta_true|) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [X] T025 [US3] Implement bootstrap resampling in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/bootstrap.py` with **at least 1,000 iterations OR until CI width variance < 0.01 is achieved (FR-005), whichever comes first**. **CRITICAL**: Set `max_iterations=1000`. **Iteration Logic**: Start with an initial set of iterations, increment by a consistent step size, up to a defined maximum. If variance < 0.01 is not achieved after max iterations, log a warning, record the final variance, and proceed with the best available CI. Do NOT fail. Record the instability in the final report. **DEPENDS ON T018**.
- [X] T028a [US3] **Implement Threshold Sensitivity Sweep Logic** (DEPENDS ON T013a, T021): Implement logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` for p-value thresholds (conventional significance levels) and imputation limits.
 1. **Threshold List**: Generate a list of thresholds for imputation limits and p-value thresholds, ranging from a minimum baseline to a maximum upper bound.
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
- [X] T029_new [US3] **Implement Family-Wise Error Correction and Final Reporting Logic** (DEPENDS ON T028b): Apply family-wise error correction (Bonferroni/Holm) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` (FR-006).
 1. **Set A (Primary Interaction)**: Apply Bonferroni correction **only** to the primary interaction hypothesis test (avatar_condition * comparison_tendency).
 2. **Set B (Sensitivity Sweeps)**: Apply Holm correction to the set of tests generated by sensitivity sweeps (thresholds + imputation limits).
 3. **Final Reporting Logic**: Report both corrected p-values separately. **Do NOT** apply Set A correction to Set B tests. **Do NOT** apply Set B correction to Set A tests. This ensures each test is corrected exactly once.
 4. **Explicit Exclusion**: Explicitly EXCLUDE model assumption tests (Shapiro, Breusch-Pagan, VIF) from both corrections.
 **DEPENDS ON T028b**.
- [X] T030 [US3] Generate final report JSON containing: data path used, model results, bootstrap stability, parameter recovery (if synthetic), and sensitivity findings (FR-012).
 1. **Action**: Explicitly write `data/processed/final_report.json`.
 2. **Artifact Schema**:
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
 3. **Validation**: Ensure all required fields are populated. If any upstream artifact is missing, write a 'partial' report with an error flag to ensure the artifact exists.
 4. **DEPENDS ON**: T025, T027, T028b, T029_new.
- [X] T030a [US3] **Interpretation Labeling Logic** (DEPENDS ON T030): Implement logic to set the `interpretation` field based on `data_source_type`. If `real`, set to "Empirical Association". If `synthetic`, set to "Simulated Causal Effect". (FR-010).
 1. **Dependency Check**: Verify `data/processed/final_report.json` exists and is non-empty. If missing, raise `ValueError`.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Documentation updates in `docs/analysis_plan.md` and `README.md`
- [X] T032a [P] Run `flake8` on `code/` and fix all errors (zero errors remaining)
- [X] T032b [P] Run `black` on `code/` and `tests/` and fix all formatting violations. **DEPENDS ON T032a**.
- [X] T033 [P] Run `pytest` on all unit and contract tests in `tests/`
- [X] T034 [P] Verify reproducibility by running `main.py` twice with fixed seeds and comparing output hashes.
 1. **Action**: Write the hash comparison results to `state/reproducibility_check.yaml` (Constitution Principle III, V).
 2. **Fallback**: If hashes cannot be compared, write a 'failed' status file to ensure the artifact exists.
 3. **DEPENDS ON**: T052.
- [X] T035 [P] Run quickstart.md validation if available

---

## Phase 7: Execution Feasibility (Streamlined)

**Purpose**: Ensure the pipeline runs successfully on the free CPU runner with dynamic resource checks.

- [X] T050 [US1] **CRITICAL**: Implement dynamic resource checking in `code/data/download.py`. Use `psutil` or `os.sysconf` to estimate available RAM. If estimated dataset size exceeds a significant proportion of available RAM, implement chunked processing or trigger a warning with explicit logging of the sampling strategy. (FR-001, Plan constraints).
- [X] T051 [US3] **CRITICAL**: Implement dynamic memory estimation in `code/analysis/bootstrap.py`. Before starting bootstrap, estimate memory usage. If estimated usage exceeds 80% of available RAM:
 1. **First**: Attempt to sample the dataset (using T066 logic) to a size that fits 1000 iterations.
 2. **Second**: If sampling is not possible or still too large, reduce iterations to the maximum possible within 80% RAM, but **MUST** log a CRITICAL warning "Statistical Power Compromised: Iterations reduced from 1000 to X due to memory constraints".
 3. **Do NOT** silently drop to 100 iterations without explicit warning.
 4. Record the actual number of iterations and the reason for reduction in `final_report.json`. (FR-005, Plan constraints).

**Checkpoint**: Pipeline is safe for execution on free CPU runner.

---

## Phase 8: Main Entry Point & Integration

**Purpose**: Create the central orchestrator that ties all components together and ensures the quickstart command works.

- [X] T052 [P] **Main Entry Point Implementation**: Create `code/main.py` in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/`. This script must:
 1. Import and execute the data discovery pipeline (T008, T009a, T009b).
 2. Trigger data loading/synthetic generation (T010, T012).
 3. Run preprocessing (T013a, T014a_new, T014b, T016, T017).
 4. Execute the ANCOVA model (T018, T019, T021, T022, T076b, T077_new).
 5. Run robustness checks (T025, T028a, T027, T029_new).
 6. Generate the final report (T030, T030a).
 7. Handle all logging and error states as defined in `code/utils/logger.py`.
 **DEPENDS ON**: All implementation tasks in Phases 1-7.
 **Artifact**: `code/main.py` executable script.

---

## Phase 9: Execution Safety & Data Integrity (Revision)

**Purpose**: Address critical review concerns regarding data loading, synthetic fallbacks, and execution safety. These tasks ensure the pipeline never fabricates data and handles real data correctly.

- [X] T063_new [US1] **Enforce Strict Real Data Fetching with Fallback** (MERGED T063/T072): Modify `code/data/download.py` (T008) to handle fetch failures gracefully.
 1. **Atomic Sequence**:
 - **Step 1 (Retry)**: If a real fetch fails due to **network error** (timeout, DNS, 500) on a **known valid source**, attempt 3 retries with exponential backoff.
 - **Step 2 (IRB Check)**: If retries fail, **MUST STILL ATTEMPT T009a (IRB Check)** on the source.
 - **Step 3 (Fallback)**: If IRB check fails OR is missing, **TRIGGER SYNTHETIC GENERATION** (T010) and write `data/raw/synthetic_seed.json` and `state/data_path_decision.yaml`.
 2. **Precedence**: This logic overrides any 'halt' condition in T009b.
 3. **Do NOT** use `try/except` to silently fall back to synthetic data for network errors on valid sources without retry/IRB check logic.
 (Constitution Principle III, FR-009, FR-011, Principle VI).
- [X] T054 [P] [US1] **Implement Verified Real Data Source Injection**: Modify `code/data/download.py` to check for a `VERIFIED_REAL_DATA_SOURCE` environment variable or config flag.
 1. **Expected Format**: A HuggingFace dataset ID (e.g., "org/dataset") or a local file path.
 2. **Validation**: If the format is invalid (does not match regex for HF ID or local path), raise a `ValueError` with message "Invalid VERIFIED_REAL_DATA_SOURCE format" and halt execution.
 3. **Action**: If present, the loader MUST use the specified package/recipe exactly, **BUT MUST STILL RUN T009a (IRB Check)** before proceeding to ensure constitutional compliance.
 (FR-009, Constitution Principle III).
- [X] T055 [P] [US1] **Add Explicit Synthetic Data Labeling**: Ensure `code/data/download.py` (T010) explicitly writes a `data_source_type` field to the output CSV and JSON artifacts, setting it to "synthetic" with a comment "Pipeline Validation Only". (FR-011).
- [X] T057 [P] [US3] **Add Bootstrap Memory Safety**: Modify `code/analysis/bootstrap.py` (T025) to include a hard limit on memory usage (e.g., 7 GB) and dynamically adjust the number of bootstrap iterations if the limit is approached. Log the adjustment and record the actual number of iterations performed. (FR-005, Plan constraints).
- [X] T058 [P] [US1] **Add Data Integrity Checksums**: Modify `code/data/download.py` (T012) to compute and store SHA-256 checksums for all downloaded real datasets and synthetic data files.
 1. **Action**: Write checksums to `state/projects/PROJ-490-the-effect-of-simulated-social-compariso.yaml` under the key `artifact_hashes`.
 2. Verify these checksums before processing.
 (Constitution Principle III).
- [X] T059 [P] [US1] **Add IRB Consent Artifact Logging**: Modify `code/data/download.py` (T009a) to log the exact **path** of any IRB/Consent artifacts found, ensuring transparency in the verification process. **Do NOT log the content** of the consent forms to preserve Data Hygiene and Ethical Human Subjects principles. (FR-009, Constitution Principle VI).
- [X] T060 [P] [US2] **Add MICE Imputation Fallback Logging**: Modify `code/data/preprocess.py` (T016) to log a detailed message if `miceforest` is unavailable and `sklearn.impute.IterativeImputer` is used, including the reason for the fallback. (FR-013).
- [X] T061 [P] [US3] **Add Sensitivity Sweep Range Validation**: Modify `code/analysis/sensitivity.py` (T028a) to validate that the sensitivity sweep range (imputation limits, p-value thresholds) is within reasonable bounds (e.g., a lower bound starting at or near zero for imputation limits) and log any adjustments made. (FR-007).
- [X] T062 [P] [US3] **Add Final Report Interpretation Validation**: Modify `code/analysis/sensitivity.py` (T030) to validate that the `interpretation` field in the final report matches the `data_source_type` (e.g., "Empirical Association" for real, "Simulated Causal Effect" for synthetic). (FR-010).

---

## Phase 10: Critical Data Hygiene & Anti-Fabrication Enforcement (Revision)

**Purpose**: Address critical review concerns regarding the strict prohibition of synthetic data fallbacks for failed real fetches and the enforcement of real data streaming.

- [X] T064 [P] [US1] **Implement Real Dataset Sampling for Large Files**: Modify `code/data/download.py` and `code/data/preprocess.py` to use `datasets.load_dataset(..., streaming=True)` for any dataset source where the estimated size exceeds 80% of available RAM.
 1. **CRITICAL**: If the dataset is too large for MICE (FR-002), **extract a representative random sample** (N >= 100, preserving missingness patterns) and run standard MICE on that sample.
 2. **Do NOT** attempt "streaming MICE" or "online imputation" as these are statistically invalid.
 3. Explicitly document the sampling strategy (seed, size, missingness preservation) in `logs/streaming.log`.
 (FR-001, Plan constraints).
- [X] T065 [P] [US1] **Add Real Data Source Verification Test**: Implement a unit test in `tests/unit/test_data_fetch.py` that simulates a network failure during a real fetch attempt and asserts that the system raises `DataFetchError` rather than generating synthetic data. This test must pass to validate the anti-fabrication constraint. (FR-009).
- [X] T066 [P] [US2] **Add Sampling Support for MICE**: Modify `code/data/preprocess.py` to support MICE imputation on sampled data chunks if the dataset is too large for memory.
 1. **Strategy**: If dataset > RAM, extract a random sample (N >= 100) and run standard MICE.
 2. **Fallback**: If sampling is not possible (e.g., N < 100 after sampling), raise an error.
 3. Explicitly log the sample size and limitation.
 (FR-002, Plan constraints).
- [X] T067 [P] [US3] **Add Bootstrap Sampling Support**: Modify `code/analysis/bootstrap.py` to support bootstrapping on sampled data chunks if the dataset is too large for memory.
 1. **Strategy**: If dataset > RAM, use the sampled data (from T064/T066) for bootstrap.
 2. **Fallback**: If sampling is not possible, reduce iterations to max possible within RAM, but log "Power Compromised" (see T051).
 (FR-005, Plan constraints).
- [X] T068 [P] [US1] **Add Real Data Checksum Verification**: Modify `code/data/download.py` to verify the SHA-256 checksum of any downloaded real dataset against a known hash stored in `state/projects/PROJ-490-the-effect-of-simulated-social-compariso.yaml` under `artifact_hashes` before processing.
 1. **Logic**: If `artifact_hashes` key is missing or the map is empty, treat this as a new file and proceed without verification.
 2. If checksum does not match, raise an error and halt **ONLY IF** the source is valid (not missing). If the checksum is missing (new file), proceed.
 3. **Do NOT** halt on missing consent (T009a handles that).
 (Constitution Principle III).
- [X] T069 [P] [US1] **Add Synthetic Data Explicit Warning**: **DELETED** (Redundant with T030/T030a).
- [X] T070 [P] [US3] **Add Sensitivity Sweep Real Data Constraint**: Modify `code/analysis/sensitivity.py` to ensure that sensitivity sweeps are only performed on real data if the dataset size allows. If the dataset is too large, implement a streaming sweep or fall back to a defined sampling strategy with explicit logging. (FR-007, Plan constraints).
- [X] T071 [P] [US1] **Add Data Fetch Retry Logic**: Modify `code/data/download.py` to implement a retry mechanism (e.g., a limited number of attempts with exponential backoff) for real data fetches before raising `DataFetchError` or triggering synthetic fallback. This ensures transient network errors do not trigger synthetic fallbacks immediately. (FR-009).
- [X] T072 [P] [US1] **Add Data Fetch Timeout Handling**: **DELETED** (Merged into T063_new).
- [X] T073 [P] [US1] **Add Data Fetch URL Validation**: Modify `code/data/download.py` to validate the URL of any real data source before attempting to fetch. Ensure the URL is a valid HuggingFace, OpenML, or OSF link. If invalid, raise `DataFetchError`. (FR-009).
- [X] T074 [P] [US1] **Add Data Fetch Metadata Verification**: Modify `code/data/download.py` to verify the metadata of any real data source (e.g., number of rows, columns) before attempting to fetch. If the metadata does not match the expected schema, raise `DataFetchError`. (FR-009).
- [X] T075 [P] [US1] **Add Data Fetch Consent Verification**: Modify `code/data/download.py` to verify the consent documentation of any real data source **after** fetching the dataset or its metadata (T009a). If consent is missing, trigger synthetic generation (T010) and log the reason. (FR-009, Constitution Principle VI).

---

## Phase 11: Execution Feasibility & Resource Constraints (New Revision Tasks)

**Purpose**: Address specific execution constraints regarding CPU-only runtime, memory limits, and the prohibition of GPU-dependent tasks in this specific pipeline context.

- [X] T078 [US3] **Optimize Bootstrap Iterations for CPU Runtime** (DEPENDS ON T025): Refine `code/analysis/bootstrap.py` to ensure the 1,000 iterations complete within the 6-hour window.
 1. **Logic**: Implement a runtime check at periodic intervals. If the estimated time to completion (using **linear extrapolation** from first 100 iterations) exceeds 5.5 hours, log a warning and **reduce remaining iterations** to fit the time budget.
 2. **Hard Fail Condition**: If iterations drop below 1,000, set `stability_status: 'failed'` in the final report AND raise a `RuntimeError` that **blocks the generation of the final report**. The report is only generated if iterations >= 1,000 or if the 'underpowered' flag is explicitly set AND the report includes a 'blocked' status.
 3. **Fallback**: If time budget is exceeded, record the number of completed iterations and the "Time-Capped" status in `final_report.json` (if not blocked).
 4. **Rationale**: Prevent the pipeline from hanging indefinitely on the free runner and ensure non-compliant results are blocked.
 (FR-005, Plan Constraints).
- [X] T079 [P] [US1] **Validate Dataset Streaming Logic**: Add a unit test in `tests/unit/test_data_fetch.py` to verify that `datasets.load_dataset(..., streaming=True)` correctly yields batches and does not load the full dataset into memory.
 1. **Test Case**: Mock a large dataset source and assert that the iterator yields small batches and that memory usage remains low.
 2. **Assertion**: Verify that the `streaming` flag is passed correctly to the dataset loader.
 (FR-001, Plan Constraints).
- [X] T080 [P] [US3] **Implement Parallel Bootstrap (Optional Optimization)**: If the environment supports multiprocessing (e.g., `multiprocessing` module), implement a parallel version of the bootstrap loop in `code/analysis/bootstrap.py`.
 1. **Logic**: Use `multiprocessing.Pool` to distribute bootstrap iterations across available CPU cores.
 2. **Safety**: Ensure random seeds are managed correctly per worker to avoid correlation.
 3. **Fallback**: If multiprocessing is unavailable or fails, revert to the single-threaded loop.
 4. **Logging**: Log the number of workers used and the speedup factor (if any).
 (FR-005, Plan Constraints).