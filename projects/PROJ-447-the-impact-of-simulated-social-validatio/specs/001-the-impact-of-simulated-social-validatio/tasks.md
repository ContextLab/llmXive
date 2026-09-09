# Tasks: The Impact of Simulated Social Validation on Self-Perception in Adolescents

**Input**: Design documents from `/specs/001-simulated-social-validation/`
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create directory structure: `code/`, `data/`, `tests/` at repository root (`projects/PROJ-447-the-impact-of-simulated-social-validatio/`)
- [ ] T001b Initialize `__init__.py` files in all created directories to make them Python packages
- [X] T002 Initialize Python 3.11 project with dependencies (`pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `semopy`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create detailed directory structure: `code/data`, `code/analysis`, `code/viz`, `code/utils`, `data/raw`, `data/processed`, `tests/unit`, `tests/integration`
- [X] T005 [P] Implement `code/utils/constants.py` with fixed random seeds and configurable thresholds (VIF, stability, significance)
- [X] T006b [P] Implement `code/utils/exceptions.py` defining custom exception classes: `DataLoadError`, `DataGapError`, `InsufficientSampleError`, `CausalLanguageViolationError`, and `StabilityThresholdViolationError` (all inheriting from `Exception`)
- [X] T006 [P] Implement `code/utils/cautions.py` containing the list of causal trigger words and a scanner function to reject reports containing them
- [X] T007 Create base configuration loader in `code/utils/config.py` to manage environment variables and file paths
- [X] T008 Setup basic logging infrastructure in `code/utils/logger.py` to track data loading, validation, and model fitting steps

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition, Validation, and Synthetic Generation (Priority: P1) 🎯 MVP

**Goal**: Successfully load/verify real data or generate synthetic data with known ground truth (SEM-based) ensuring longitudinal match and required columns.

**Independent Test**: The pipeline can be tested by attempting to load the specified dataset (real or synthetic) and checking for the presence of required columns (engagement counts, Rosenberg Self-Esteem Scale scores, comment sentiment scores, and temporal ordering).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for `code/data/generator.py` verifying that synthetic data converges to target SEM parameters in `tests/unit/test_generator.py` <!-- ATOMIZE: requested -->
- [X] T010 [P] [US1] Unit test for `code/data/validator.py` verifying that missing data (N < 100) or missing longitudinal order triggers a specific error in `tests/unit/test_validator.py`

### Implementation for User Story 1

- [X] T011a [P] [US1] Add `semopy` library to `requirements.txt` and verify installation for SEM implementation
- [X] T011 [US1] Implement `code/data/generator.py` to create synthetic data using a Structural Equation Model (SEM) via `semopy` that explicitly models measurement error and reverse causality, ensuring `device="cpu"` compatibility
- [X] T011b [US1] Implement verification logic in `code/data/generator.py` to confirm the synthetic data recovers the *observed* association parameters (as defined in the Plan's 'Key Methodological Correction') rather than just the latent causal beta, and log this verification
- [X] T015a [P] [US1] Define the mathematical formula, weights, and logic for the 'Perceived Social Validation' measurement model in `code/utils/constants.py` (referenced by FR-008)
- [ ] T015 [US1] Implement `code/data/processor.py` to apply FR-008: Derive 'Perceived Social Validation' from engagement metrics and comment sentiment using the mathematical formula defined in `code/utils/constants.py` (T015a)
- [X] T012 [US1] Implement `code/data/loader.py` to attempt fetching real datasets. **CRITICAL**: Must raise a custom `DataLoadError` with a standardized message format (e.g., "DataLoadError: Failed to fetch real dataset from [URL]") on failure; NO synthetic fallback in the loader itself (fallback handled by orchestration)
- [X] T013 [US1] Implement `code/data/validator.py` to check for: (1) Presence of engagement metrics, sentiment scores, and psychometric scales; (2) Distinct handling: If N=0, raise `DataGapError` (specific to zero rows); If 0<N<100, raise `InsufficientSampleError`; (3) Longitudinal ordering (engagement timestamp < self-report timestamp)
- [X] T014 [US1] Implement `code/main.py` orchestration logic:
 1. Attempt real load via `loader.py` (T012).
 2. If `DataLoadError` is caught, immediately invoke `generator.py` (T011) to create synthetic data.
 3. Pass the resulting data to `validator.py` (T013).
 4. If validation fails (N=0), raise `DataGapError`; if 0<N<100, raise `InsufficientSampleError`.
 5. Generate `data/processed/pipeline_run_log.json` with status codes.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Analysis (Priority: P2)

**Goal**: Run multiple linear regression with confounders, calculate VIF, and ensure "associational" framing.

**Independent Test**: The analysis can be tested by running the regression on a synthetic dataset with known coefficients and verifying that the model recovers the correct coefficients and p-values within a small tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for `code/analysis/regression.py` verifying coefficient recovery on synthetic data with known ground truth in `tests/unit/test_regression.py`
- [X] T017 [P] [US2] Unit test for `code/utils/cautions.py` verifying that a report with "causes" is flagged and rejected in `tests/unit/test_cautions.py`

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement `code/analysis/regression.py` to fit a multiple linear regression model (Outcome: Self-Perception; Predictors: Engagement, Age, Gender, Offline Relationships, Intrinsic Traits) using `statsmodels`
- [~] T019 [US2] Implement VIF calculation in `code/analysis/regression.py` to detect multicollinearity for all predictors, **write the calculated VIF values, the threshold value from `constants.py`, and the comparison status (e.g., "PASS"/"FAIL") to `data/processed/model_results.json` with keys `vif_value`, `threshold_value`, `status`**, and flag if exceeding threshold
- [X] T020 [US2] Implement output formatting in `code/analysis/regression.py` to ensure all findings are labeled "associational". **First, generate a draft report buffer in memory**, then run the causal language scanner on this buffer; **if any trigger word is found, raise `CausalLanguageViolationError` (imported from `code/utils/exceptions.py`) to halt the pipeline (integrated with T028)**.
- [~] T021 [US2] Integrate regression results into `code/main.py` to save model coefficients, p-values, confidence intervals, and VIF scores to `data/processed/model_results.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness, Sensitivity, and Visualization (Priority: P3)

**Goal**: Verify stability against outliers/confounders, check non-linearity, and generate diagnostic plots.

**Independent Test**: The robustness check can be tested by artificially introducing outliers or toggling confounders and verifying the system reports the sensitivity of the results.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Integration test for sensitivity analysis verifying that coefficient variation is calculated correctly across strategies in `tests/integration/test_sensitivity.py`
- [ ] T023 [P] [US3] Unit test for `code/viz/plots.py` verifying that scatter and residual plots are generated and saved to disk in `tests/unit/test_plots.py`

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement `code/analysis/sensitivity.py` to re-run the regression with **three outlier strategies (none, IQR removal, winsorization) AND with critical confounders included/excluded (creating a 3x2 matrix of runs)**, reporting the variation in the primary coefficient for each strategy
- [ ] T025a [P] [US3] Implement `code/utils/exceptions.py` (if not already done) to define `StabilityThresholdViolationError` class inheriting from `Exception`
- [ ] T025 [US3] Implement logic in `code/analysis/sensitivity.py` to calculate the variation in the primary coefficient, **read the stability threshold from `code/utils/constants.py`**, and **if the variation exceeds the threshold, raise `StabilityThresholdViolationError` (imported from `code/utils/exceptions.py`) to halt the pipeline**.
- [ ] T026 [P] [US3] Implement `code/analysis/nonlinearity.py` to fit a quadratic term for the primary predictor and report its significance
- [ ] T027 [US3] Implement `code/viz/plots.py` to generate: (1) Scatter plot with regression line; (2) Residual diagnostic plot; (3) Save as PNG files in `data/processed/` with exact filenames: `scatter_plot.png`, `residuals.png`
- [ ] T027a [US3] Implement logic to count the number of generated visualization files in `data/processed/` and validate the count against the minimum set requirement (SC-005), raising an error if the count is insufficient
- [ ] T028 [US3] Update `code/main.py` to execute sensitivity and non-linearity checks after the primary model. **Explicitly catch `CausalLanguageViolationError` (from T020) and `StabilityThresholdViolationError` (from T025), and halt the pipeline immediately if either is raised.** Aggregate all results into a final report.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T030 Code cleanup and refactoring to ensure type hinting and docstrings; **verify pass with `ruff check` (zero errors) and `black --check` (zero diffs)**
- [ ] T031 Performance optimization (ensure data processing fits within available system memory constraints); **verify peak memory usage < 6GB during synthetic generation**
- [ ] T032 [P] Additional unit tests for edge cases (e.g., zero rows, missing demographics) in `tests/unit/`
- [ ] T033 Security hardening: Ensure no PII is written to logs or outputs
- [ ] T034 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
 - **Execution Flow**: T014 (Orchestrator) calls T012 (Loader). If T012 fails, T014 calls T011 (Generator). T014 then calls T013 (Validator). T015a (Define Model) and T015 (Implement Model) are prerequisites for T014's data processing.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data availability
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model results

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (data generators before validators)
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
Task: "Unit test for code/data/generator.py verifying that synthetic data converges to target SEM parameters in tests/unit/test_generator.py"
Task: "Unit test for code/data/validator.py verifying that missing data (N < 100) or missing longitudinal order triggers a specific error in tests/unit/test_validator.py"

# Launch all models for User Story 1 together (Note: T014 is the entry point):
Task: "Implement code/main.py orchestration logic (T014) which calls T012, T011, T013, T015"
Task: "Implement code/data/generator.py (T011)..."
Task: "Implement code/data/processor.py (T015)..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Pipeline)
4. **STOP and VALIDATE**: Test User Story 1 independently (Real data load OR Synthetic generation with validation)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Core Analysis)
4. Add User Story 3 → Test independently → Deploy/Demo (Robustness & Viz)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Statistical Modeling)
 - Developer C: User Story 3 (Robustness & Viz)
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
- **Data Hygiene**: `code/data/loader.py` (T012) MUST fail loudly on real data fetch failure by raising `DataLoadError` with a standardized message; synthetic generation is only invoked by `code/main.py` (T014) orchestration, not as a silent fallback. T014 guarantees the "automatic" invocation.
- **Compute Constraints**: All data processing must fit within a constrained memory footprint consistent with standard workstation capabilities.; use streaming or chunking if necessary (though synthetic data is expected to be < 1GB).
- **Causal Language**: The `cautions.py` scanner is mandatory for FR-006; any report containing "causes", "leads to", etc., must trigger `CausalLanguageViolationError` (T020) and halt.
- **Stability**: Coefficient variation exceeding the threshold must trigger `StabilityThresholdViolationError` (T025) and halt (T028).
- **Measurement Model**: The formula for 'Perceived Social Validation' is defined in `constants.py` (T015a) before implementation (T015).
- **SEM Library**: The plan requires `semopy` for SEM implementation; ensure it is installed and used in T011.
- **Sensitivity Analysis**: T024 MUST implement the full 3x2 matrix (3 outlier strategies x 2 confounder states) to satisfy FR-004.
- **VIF Verification**: T019 MUST log the comparison result (value, threshold, status) to satisfy SC-002.
- **Exception Handling**: All custom exceptions are defined in `code/utils/exceptions.py` (T006b).