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

- [X] T001 [P] Initialize project structure: Create root directory `projects/PROJ-490-the-effect-of-simulated-social-compariso/` and subdirectories `code/`, `data/`, `tests/`, `docs/`, `state/`, `data/raw`, `data/processed`, `tests/contract`, `tests/unit`. Create `requirements.txt`, `README.md`, and configure linting (flake8/pylint) and formatting (black) tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

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
- [X] T009a [US1] Implement IRB/Consent verification script in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` (DEPENDS ON T008 output): <!-- FAILED: unspecified -->
 1. Check for existence of IRB/Consent artifact in `data/raw/consent_forms/`.
 2. Verify the artifact by checking for keywords 'IRB' or 'Consent' in the filename or metadata.
 3. Log specific findings to `logs/irb_check.log`.
 **Artifact**: No standalone artifact; produces log entries.
- [X] T009b [US1] Implement fallback trigger logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` (DEPENDS ON T009a):
 1. If valid IRB/Consent documentation is NOT found AND real data exists, trigger synthetic generation (T010) and log the specific missing consent URL.
 2. If no real data is found by T008, allow T010 to trigger synthetic generation.
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
- [X] T012 [P] [US1] Create `data/raw` loader that saves downloaded CSVs or synthetic outputs and writes checksums to `state/projects/PROJ-490-the-effect-of-simulated-social-compariso.yaml` under `artifact_hashes` (Constitution Principle III, V).
- [ ] T013a [US1] **Pre-Imputation Variable Check** (DEPENDS ON T012, T009b): Verify `data/raw` contains ALL required variables (avatar_condition, pre_self_esteem, post_self_esteem, comparison_tendency) BEFORE imputation. If any are missing, trigger T010 (Synthetic). Write validation status to `data/processed/pre_imputation_validation.json`.
 **Artifact Schema**:
 ```json
 {
 "status": "pass" | "fail",
 "missing_vars": [],
 "timestamp": "ISO8601"
 }
 ```
 (FR-009).
- [ ] T013b [US1] **Post-Imputation Validation** (DEPENDS ON T016a): Verify `data/processed/imputed_data.csv` contains clean data after T016a. Write validation status to `data/processed/post_imputation_validation.json`. **Success Condition**: File exists, is non-empty, and row count matches expected input (minus excluded rows).
 **Artifact Schema**:
 ```json
 {
 "status": "pass" | "fail",
 "imputation_success": true | false,
 "timestamp": "ISO8601"
 }
 ```

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (data path selected and validated).

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline (Priority: P2)

**Goal**: Preprocess data (MICE), fit ANCOVA regression, and validate model assumptions.

**Independent Test**: Can be fully tested by running the complete analysis pipeline on a sample dataset (real or synthetic) and producing reproducible output artifacts (a CSV file containing regression coefficients and a JSON file containing diagnostic metrics) within ≤6 hours on CPU-only hardware.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T014 [P] [US2] Contract test for regression output schema in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/contract/test_results_schema.py`
- [X] T015 [P] [US2] Unit test for MICE imputation on missing < 20% vs > 20% exclusion logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/unit/test_preprocess.py`

### Implementation for User Story 2

- [X] T014a [US2] **Sample Size Enforcement** (DEPENDS ON T013a): Implement logic in `code/data/preprocess.py` to check N ≥ 100 (FR-001). If N < 100, raise `ValueError` with message "Sample size < 100".
- [X] T014b [US2] **MICE Exclusion Logic** (DEPENDS ON T013a): Implement logic in `code/data/preprocess.py` to count missingness per row. If a row has > 20% missingness across key variables, exclude it from imputation (FR-002). Log excluded row IDs.
- [ ] T016 [US2] Implement missing data handling in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/preprocess.py` using `miceforest` (primary) for < 20% missingness; fallback to `sklearn.impute.IterativeImputer` if `miceforest` unavailable; exclude rows with > 20% (FR-002, FR-013). **DEPENDS ON T012, T013a, T014a, T014b**. Perform imputation in memory. **CRITICAL OUTPUT**: Explicitly save the resulting imputed DataFrame to `data/processed/imputed_data.csv` to satisfy T013b and T016a requirements.
- [ ] T016a [US2] **Write Imputed Data to Disk** (DEPENDS ON T016): Save the imputed DataFrame to `data/processed/imputed_data.csv`. **CRITICAL**: This task explicitly writes the artifact required by T013b. (FR-002, FR-013).
- [X] T016b [US2] **Imputation Fallback Logic** (DEPENDS ON T016): Implement explicit try/except block in `code/data/preprocess.py` to detect `miceforest` unavailability (ImportError) and automatically switch to `sklearn.impute.IterativeImputer`. Log the switch event. (FR-013).
- [X] T017 [US2] Implement variable normalization (avatar_condition to 0/1 if binary) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/preprocess.py` AND compute change scores (post_self_esteem - pre_self_esteem) **strictly for in-memory logging/diagnostics ONLY**. **CRITICAL**: DO NOT use change scores as the model outcome. The primary model must use ANCOVA (outcome: post_self_esteem, covariate: pre_self_esteem) to avoid mathematical coupling as mandated by the Plan. **DO NOT persist change scores to disk**. Log a warning in `logs/preprocess.log` that these are for descriptive use only. **DEPENDS ON T013a, T016a**. **Note**: This task is non-blocking; if change score calculation fails, log a warning and proceed. Downstream tasks (T013b, T022) depend on the *imputed dataset* (from T016a), not the change score.
- [X] T018 [US2] Implement ANCOVA regression model in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/regression.py` (outcome: post_self_esteem, covariate: pre_self_esteem, predictors: avatar_condition, comparison_tendency, interaction). Explicitly document in code comments that this implements the ANCOVA approach (avoiding mathematical coupling) as mandated by the Plan. **DEPENDS ON T013a, T016a**.
- [X] T018a [US2] **ANCOVA Constraint Verification** (DEPENDS ON T018): Add unit test in `tests/unit/test_preprocess.py` to assert that `post_self_esteem` is the outcome and `pre_self_esteem` is the covariate in the model formula. Ensure no change scores are used as the outcome variable.
- [X] T019 [US2] Implement assumption validation in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/regression.py`: Shapiro-Wilk (normality), Breusch-Pagan (homoscedasticity), VIF (collinearity) (FR-004).
- [ ] T021 [US2] Export regression coefficients to `data/processed/regression_coefficients.csv` and diagnostics (p-values, VIF, CI) to `data/processed/model_diagnostics.json` (FR-008).
- [X] T022 [US2] Handle collinearity (VIF ≥ 5) by flagging and framing results descriptively without claiming independent effects. Update `data/processed/model_diagnostics.json` with `collinearity_warning` key (Assumptions).

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
- [ ] T028a [US3] Implement threshold sensitivity sweep in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` for p-value thresholds (conventional significance levels) and imputation limits. **Sweep imputation limits from 0.0 to 0.20 with a maximum of 10 distinct thresholds (dynamic step size: min(0.05, 0.20/10))** (FR-007). **Explicitly includes the complete case baseline** as required by the spec. **Note**: The implementation must use a predefined 'low' threshold and log this choice in `logs/sensitivity.log` to ensure transparency. **DEPENDS ON T013a, T051**. **Artifact**: `data/processed/sensitivity_sweep_results.csv` containing columns `[threshold, bias, variance, baseline_id]`.
- [X] T028b [US3] Implement sensitivity sweep logging in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` (DEPENDS ON T028a). Log the sweep range and parameters to `logs/sensitivity.log`.
- [X] T027 [US3] Implement parameter recovery analysis in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` for synthetic data: compare estimated coefficients to ground truth (FR-011, SC-005).
- [X] T029 [US3] Apply family-wise error correction (Bonferroni/Holm) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` (FR-006): Apply correction **only** to the set of tests generated by sensitivity sweeps (thresholds + imputation limits) and the primary interaction effect hypothesis test. **Explicitly EXCLUDE model assumption tests (Shapiro, Breusch-Pagan, VIF)** as these are diagnostic checks, not research hypotheses. **DEPENDS ON T028a**.
- [ ] T029a [US3] **Primary Interaction Error Correction** (DEPENDS ON T029): Implement explicit Bonferroni/Holm correction logic for the **primary interaction hypothesis test** (avatar_condition * comparison_tendency) in `code/analysis/sensitivity.py`. Ensure the corrected p-value is recorded in the final report. (FR-006).
- [ ] T030 [US3] Generate final report JSON containing: data path used, model results, bootstrap stability, parameter recovery (if synthetic), and sensitivity findings (FR-012). Write to `data/processed/final_report.json`.
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
- [ ] T034 Verify reproducibility by running `main.py` twice with fixed seeds and comparing output hashes. Writes the hash comparison results to `state/reproducibility_check.yaml` (Constitution Principle III, V).
- [X] T035 Run quickstart.md validation if available

---

## Phase 7: Execution Feasibility (Streamlined)

**Goal**: Ensure the pipeline runs successfully on the free CPU runner with dynamic resource checks.

- [ ] T050 [US1] **CRITICAL**: Implement dynamic resource checking in `code/data/download.py`. Use `psutil` or `os.sysconf` to estimate available RAM. If estimated dataset size exceeds a significant proportion of available RAM, implement chunked processing or trigger a warning with explicit logging of the sampling strategy. **NO hardcoded thresholds**. (FR-001, Plan constraints).
- [ ] T051 [US3] **CRITICAL**: Implement dynamic memory estimation in `code/analysis/bootstrap.py`. Before starting bootstrap, estimate memory usage. If estimated usage exceeds 80% of available RAM, reduce iterations to a minimum of 100 and log the reduction. Record the actual number of iterations and the reason for reduction in `final_report.json`. (FR-005, Plan constraints).

**Checkpoint**: Pipeline is safe for execution on free CPU runner.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Execution Feasibility (Phase 7)**: Depends on US1 and US3 implementation; must be completed before final execution to ensure data safety and resource management.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires model from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Unit test for synthetic data generator parameter recovery in tests/unit/test_synthetic_gen.py"

# Launch all models for User Story 1 together:
Task: "Implement dataset discovery script in code/data/download.py"
Task: "Implement synthetic data generator in code/data/download.py"
```

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

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Tasks T050-T051 are mandatory for execution feasibility and must be implemented to ensure the pipeline runs successfully on the free CPU runner. They address compute limits and memory safety with dynamic, spec-compliant checks.
- **CRITICAL**: T016a is mandatory to ensure the artifact required by T013b is generated.
- **CRITICAL**: T025 must include a max iteration limit to prevent infinite loops.
- **CRITICAL**: T028a must use dynamic step size to ensure compliance with the 6-hour compute constraint.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T052 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
