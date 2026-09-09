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

- [ ] T002 [P] Create schema contracts in `projects/PROJ-490-the-effect-of-simulated-social-compariso/contracts/` (dataset.schema.yaml, output.schema.yaml, results.schema.yaml). **Explicit Definitions**:
  - **dataset.schema.yaml**: Create this file with the following exact content:
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
  - **output.schema.yaml**: Create this file with the following exact content:
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
  - **results.schema.yaml**: Create this file with the following exact content:
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
  - All schemas must include validation rules for N ≥ 100 participants (FR-001).
- [X] T003 [P] Implement schema validation utilities in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/utils/validators.py`
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

- [X] T008 [P] [US1] Implement dataset discovery script in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` to query HuggingFace, OpenML, and OSF for RSES/INCOM/PrePost variables.
- [X] T009 [US1] Implement robust IRB/Consent verification logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` (DEPENDS ON T008 output):
  1. If real data is found: Check metadata for 'consent_form_url'.
  2. If a URL is found, perform an HTTP GET request; if status == 200 and the content (or filename) contains keywords like 'IRB', 'Consent', or file extensions '.pdf', '.docx', mark as verified.
  3. If valid IRB/Consent documentation is NOT found AND real data exists, **trigger synthetic generation (T011)** and log the specific missing consent URL. Do NOT block the pipeline; treat missing IRB as a reason to fallback to synthetic data per FR-011.
  4. If no real data is found by T008, T009 MUST NOT block; it must allow T011 to trigger synthetic generation.
  5. Log specific findings to `logs/irb_check.log`. This ensures the ethical constraint is enforced without falsely blocking valid datasets or preventing the synthetic fallback when no real data exists. (Constitution Principle VI, FR-011, FR-014).
- [X] T010 [P] [US1] Implement synthetic data generator in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/download.py` with N ≥ 100, interaction β = 0.2, and "Pipeline Validation Only" labeling (FR-011). **Ground Truth Parameters**: intercept=0, main_effect_avatar=0.1, main_effect_comparison=0.1, interaction_beta=0.2, noise_sigma=1.0. All values must be hardcoded or loaded from a config file to ensure reproducibility.
- [X] T011 [US1] Implement fallback logic: DEPENDS ON T009, T010. If real data not found OR if IRB/Consent verification fails (via T009) OR if required variables are missing, trigger synthetic generation (call T010), set `data_source_type=synthetic` in `state/projects/PROJ-490-the-effect-of-simulated-social-compariso.yaml`, and generate `data/raw/synthetic_seed.json` (FR-009).
- [X] T012 [P] [US1] Create `data/raw` loader that saves downloaded CSVs or synthetic outputs and writes checksums to `state/projects/PROJ-490-the-effect-of-simulated-social-compariso.yaml` under `artifact_hashes` (Constitution Principle III, V).
- [X] T013a [US1] **Pre-Imputation Variable Check**: Verify `data/raw` contains ALL required variables (avatar_condition, pre_self_esteem, post_self_esteem, comparison_tendency) BEFORE imputation. If any are missing, trigger T011 (Synthetic). DEPENDS ON T012. Write validation status to `data/processed/pre_imputation_validation.json`. (FR-009).
- [X] T013b [US1] **Post-Imputation Validation**: Verify `data/processed/imputed_data.csv` contains clean data after T016. DEPENDS ON T016. Write validation status to `data/processed/post_imputation_validation.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (data path selected and validated).

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline (Priority: P2)

**Goal**: Preprocess data (MICE), fit ANCOVA regression, and validate model assumptions.

**Independent Test**: Can be fully tested by running the complete analysis pipeline on a sample dataset (real or synthetic) and producing reproducible output artifacts (a CSV file containing regression coefficients and a JSON file containing diagnostic metrics) within ≤6 hours on CPU-only hardware.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T014 [P] [US2] Contract test for regression output schema in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/contract/test_results_schema.py`
- [X] T015 [P] [US2] Unit test for MICE imputation on missing < 20% vs > 20% exclusion logic in `projects/PROJ-490-the-effect-of-simulated-social-compariso/tests/unit/test_preprocess.py`

### Implementation for User Story 2

- [X] T016 [US2] Implement missing data handling in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/preprocess.py` using `miceforest` (primary) for < 20% missingness; fallback to `sklearn.impute.IterativeImputer` if `miceforest` unavailable; exclude rows with > 20% (FR-002, FR-013). **DEPENDS ON T012, T013a**. Output to `data/processed/imputed_data.csv`.
- [X] T017 [US2] Implement variable normalization (avatar_condition to 0/1 if binary) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/data/preprocess.py` AND compute change scores (post_self_esteem - pre_self_esteem) **strictly for descriptive/logging purposes ONLY**. **CRITICAL**: DO NOT use change scores as the model outcome. The primary model must use ANCOVA (outcome: post_self_esteem, covariate: pre_self_esteem) to avoid mathematical coupling as mandated by the Plan. **DEPENDS ON T013a, T016**. Write change scores to `data/processed/descriptive_change_scores_log.csv` and log a warning in `logs/preprocess.log` that these are for descriptive use only.
- [X] T018 [US2] Implement ANCOVA regression model in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/regression.py` (outcome: post_self_esteem, covariate: pre_self_esteem, predictors: avatar_condition, comparison_tendency, interaction). Explicitly document in code comments that this implements the ANCOVA approach (avoiding mathematical coupling) as mandated by the Plan. **DEPENDS ON T013a, T016**.
- [X] T019 [US2] Implement assumption validation in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/regression.py`: Shapiro-Wilk (normality), Breusch-Pagan (homoscedasticity), VIF (collinearity) (FR-004).
- [X] T020 [US2] Implement dynamic interpretation logic: "Empirical Association" for real data vs "Simulated Causal Effect" for synthetic data. DEPENDS ON T019. Append interpretation string to `data/processed/final_report.json` (FR-010).
- [X] T021 [US2] Export regression coefficients to `data/processed/regression_coefficients.csv` and diagnostics (p-values, VIF, CI) to `data/processed/model_diagnostics.json` (FR-008).
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

- [X] T025 [US3] Implement bootstrap resampling in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/bootstrap.py` with **at least 1,000 (Wikipedia: Bootstrapping (statistics), https://en.wikipedia.org/wiki/Bootstrapping_(statistics)) iterations** OR **until CI width variance < 0.01** is achieved (FR-005). This ensures a concrete stopping criterion for executability.
- [X] T026 [US3] Calculate CI width variance from bootstrap results; **do NOT raise an exception**. Instead, if CI width variance >= 0.01, set a `stability_failed` flag to `true` and write the variance value to `data/processed/final_report.json`. If variance < 0.01, set `stability_failed` to `false`. This ensures the pipeline completes and reports the stability status as a finding (SC-004). **DEPENDS ON T025**.
- [X] T027 [US3] Implement parameter recovery analysis in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` for synthetic data: compare estimated coefficients to ground truth (FR-011, SC-005).
- [X] T028 [US3] Implement threshold sensitivity sweep in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` for p-value thresholds (conventional significance levels) and imputation limits **{complete_case (0.0), 0.05, 0.15, 0.20}** (FR-007). **Explicitly includes the complete case baseline** as required by the spec. **Note**: The implementation must use the exact value 0.05 for the 'low' threshold and log this choice in `logs/sensitivity.log` to ensure transparency. **DEPENDS ON T013a** (for complete case data).
- [X] T029 [US3] Apply family-wise error correction (Bonferroni/Holm) in `projects/PROJ-490-the-effect-of-simulated-social-compariso/code/analysis/sensitivity.py` (FR-006): Apply correction **only** to the set of tests generated by sensitivity sweeps (thresholds + imputation limits) and the primary interaction effect hypothesis test. **Do NOT apply correction to model assumption tests (Shapiro, Breusch-Pagan, VIF)** as these are diagnostic checks, not research hypotheses.
- [X] T030 [US3] Generate final report JSON containing: data path used, model results, bootstrap stability, parameter recovery (if synthetic), and sensitivity findings (FR-012). Write to `data/processed/final_report.json` with keys: `data_source_type`, `model_coefficients`, `bootstrap_ci_variance`, `parameter_recovery_bias` (if synthetic), `sensitivity_results`, `stability_failed` (boolean).

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Documentation updates in `docs/analysis_plan.md` and `README.md`
- [X] T032a [P] Run `flake8` on `code/` and fix all errors (zero errors remaining)
- [X] T032b [P] Run `black` on `code/` and `tests/` and fix all formatting violations. DEPENDS ON T032a.
- [X] T033 [P] Run `pytest` on all unit and contract tests in `tests/`
- [X] T034 Verify reproducibility by running `main.py` twice with fixed seeds and comparing output hashes. Writes the hash comparison results to `state/reproducibility_check.yaml` (Constitution Principle III, V).
- [X] T035 Run quickstart.md validation if available

---

## Phase 7: Data Integrity & Execution Safety (Revision Concerns)

**Goal**: Address critical execution risks regarding data loading, synthetic fallbacks, and compute feasibility identified in prior reviews.

- [X] T036 [US1] **CRITICAL**: Refactor `code/data/download.py` to ensure **NO** `try/except` blocks or `if download_failed:` logic fall back to `generate_synthetic_*()` or `mock_*()` data when a real fetch fails. A failed real fetch (e.g., network error, 404 on a specific URL) MUST raise an explicit exception (e.g., `DataFetchError`). **HOWEVER**, if the systematic search (T008) confirms **NO** real datasets exist across HuggingFace, OpenML, and OSF (i.e., "not found" rather than "fetch failed"), the system MUST proceed to T011 (Synthetic). T036 must distinguish between "fetch error" (raise) and "no data found" (fallback). (Constitution Principle: Real data + real results only). **DELIVERABLE**: The code must define and raise `DataFetchError` on network failures.
- [X] T037 [US1] **CRITICAL**: Implement explicit "Stream vs. Sample" logic in `code/data/download.py`. If a real dataset is identified but exceeds available memory capacity, implement `datasets.load_dataset(..., streaming=True)` and iterate in chunks to accumulate statistics online. Only if streaming is impossible should a well-defined sample (e.g., `itertools.islice` first N rows) be used, and the code MUST explicitly log the sample size and its limitations. **NEVER** swap in a bundled toy dataset.
- [X] T038 [US1] **CRITICAL**: Add a "Verified Real Data Source" check. If the execution feedback contains a "VERIFIED REAL DATA SOURCE" block, `code/data/download.py` MUST adopt that exact package/recipe as the single source, removing any hand-rolled `load_dataset("<guessed-id>")` or guessed URLs.
- [X] T039 [US1] **CRITICAL**: Ensure the synthetic data generator (T010) is **ONLY** triggered if: (a) The systematic search (T008) finds no real datasets, OR (b) Real datasets exist but lack IRB/Consent (T009), OR (c) Real datasets lack required variables. The code MUST log the specific reason for synthetic generation in `logs/data_path_decision.log`. **Implementation Detail**: Write the log entry as a JSON object with keys: `reason`, `timestamp`, `source` (e.g., `{"reason": "missing_irb", "timestamp": "2024-01-15T10:00:00Z", "source": "dataset_xyz"}`). **DELIVERABLE**: Ensure `logging.info` or `logging.warning` is explicitly called in the code at the point of fallback.
- [X] T040 [US2] **CRITICAL**: Verify that the ANCOVA model implementation (T018) does not inadvertently use change scores as the outcome variable, which would violate the "avoid mathematical coupling" constraint. Add a unit test in `tests/unit/test_preprocess.py` to assert that `post_self_esteem` is the outcome and `pre_self_esteem` is the covariate in the model formula.
- [X] T041 [US3] **CRITICAL**: Ensure the bootstrap resampling (T025) uses a deterministic random seed for reproducibility, and that the stopping criterion (CI width variance < 0.01) is logged with the exact number of iterations performed. If the limit (e.g., a predefined maximum number of iterations) is reached without meeting the criterion, the pipeline must log a warning but **NOT** fail, recording the final variance in `data/processed/final_report.json`.
- [X] T042 [US3] **CRITICAL**: Ensure the sensitivity analysis (T028) explicitly tests the **complete case** baseline (no imputation) as a distinct condition in the threshold sweep, and reports the bias/variance relative to this baseline. **Implementation Detail**: Write a CSV file `data/processed/sensitivity_baseline_comparison.csv` containing columns `[threshold, bias, variance, baseline_id]` where `baseline_id` is the ID of the complete case run.
- [X] T043 [US1] **CRITICAL**: Implement a strict "Fail Loudly" policy in `code/data/download.py`. Remove any logic that silently substitutes synthetic data on network errors. If `load_dataset` or a raw URL fetch raises an exception, the script must crash immediately with a clear error message indicating the specific URL or dataset ID that failed, preventing the pipeline from proceeding with fake data. **DELIVERABLE**: Code must raise `DataFetchError` with a descriptive message on any fetch exception.
- [X] T044 [US1] **CRITICAL**: Add a pre-flight check in `code/data/download.py` to validate that any real dataset URL or HuggingFace ID used is reachable before attempting to load it. If a URL returns a 403/404, log the failure and trigger the "no data found" path (leading to synthetic generation) rather than attempting a retry that might hang or succeed with a different (invalid) resource. **DELIVERABLE**: Code must raise `ValueError` if IRB/Consent is missing for a found dataset, preventing silent fallback.
- [X] T045 [US2] **CRITICAL**: Ensure the MICE imputation (T016) handles the `comparison_tendency` variable correctly. If this variable has > 20% missingness, the entire row must be excluded per FR-002, not imputed. Add a specific check in `code/data/preprocess.py` to count missingness per variable before imputation and log the exclusion count.
- [X] T046 [US3] **CRITICAL**: Verify that the bootstrap resampling (T025) is computationally feasible within the 6-hour CPU limit. If 1,000 iterations with the full dataset exceed the time limit, implement a dynamic reduction strategy that logs the reduction and the resulting CI width variance, ensuring the pipeline completes without fabricating results.
- [ ] T047 [US1] **CRITICAL**: Create unit test `tests/unit/test_data_fetch_errors.py` that explicitly asserts the "Fail Loudly" behavior. The test must mock a network failure (404/500) and verify that the `DataFetchError` exception is raised immediately, ensuring no silent fallback to synthetic data occurs. (Addresses T036, T043 verification). **DELIVERABLE**: A pytest file that mocks `requests.get` or `load_dataset` to raise an exception and asserts `with pytest.raises(DataFetchError): ...`.
- [ ] T048 [US1] **CRITICAL**: Create unit test `tests/unit/test_irb_validation.py` that asserts the "Fail Loudly" behavior for missing IRB. The test must provide a mock dataset with `consent_form_url` pointing to a non-existent file or missing metadata and verify that a `ValueError` is raised (or synthetic fallback is triggered explicitly) without silent data generation. (Addresses T009, T044 verification). **DELIVERABLE**: A pytest file that asserts `ValueError` is raised when IRB is missing.
- [ ] T049 [US1] **CRITICAL**: Create unit test `tests/unit/test_variable_validation.py` that asserts the "Fail Loudly" behavior for missing variables. The test must provide a mock dataset missing a required column (e.g., `comparison_tendency`) and verify that a `FileNotFoundError` or `ValueError` is raised immediately, preventing the pipeline from proceeding with incomplete data. (Addresses T013a, T039 verification). **DELIVERABLE**: A pytest file that asserts `ValueError` is raised when required variables are missing.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Integrity (Phase 7)**: Depends on Foundational and US1 implementation; must be completed before final execution to ensure data safety.

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
- **CRITICAL**: Tasks T036-T049 are mandatory for data integrity and must be implemented before the pipeline is considered production-ready. They address specific risks of fabrication, synthetic fallback, and data handling.