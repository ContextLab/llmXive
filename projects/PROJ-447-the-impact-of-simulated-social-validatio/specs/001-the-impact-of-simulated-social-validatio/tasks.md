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

- [X] T001a Create directory `projects/PROJ-447-the-impact-of-simulated-social-validatio/code/` at repository root.
- [X] T001b Create directory `projects/PROJ-447-the-impact-of-simulated-social-validatio/data/` at repository root.
- [X] T001c Create directory `projects/PROJ-447-the-impact-of-simulated-social-validatio/tests/` at repository root.
- [X] T001d Create detailed subdirectories: `code/data`, `code/analysis`, `code/viz`, `code/utils`, `data/raw`, `data/processed`, `tests/unit`, `tests/integration`.
- [X] T002 Initialize `__init__.py` files in all created directories to make them Python packages.
- [X] T003 Configure linting and formatting tools: Create `.ruff.toml` and `pypy.toml` at repository root with pinned versions for `ruff` and `black` to satisfy Constitution Principle I (Reproducibility).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `code/utils/constants.py` with fixed random seeds and configurable thresholds (VIF, stability, significance).
- [X] T005b [P] [US1] Set the `stability_threshold` key in `code/utils/constants.py` to a concrete float value within an empirically determined range appropriate for the system's stability. This value is pre-registered as per FR-004 and SC-003 to ensure deterministic stability checks.
- [X] T006b [P] Implement `code/utils/exceptions.py` defining custom exception classes: `DataLoadError`, `DataGapError`, `InsufficientSampleError`, `CausalLanguageViolationError`, `StabilityThresholdViolationError`, and `LongitudinalMismatchError` (all inheriting from `Exception`).
- [X] T006 [P] Implement `code/utils/cautions.py` containing the list of causal trigger words and a scanner function to reject reports containing them.
- [X] T007 Create base configuration loader in `code/utils/config.py` to manage environment variables and file paths.
- [X] T008 Setup basic logging infrastructure in `code/utils/logger.py` to track data loading, validation, and model fitting steps.
- [X] T015a [P] [US1] Define the mathematical formula structure for the 'Perceived Social Validation' measurement model in `code/utils/constants.py`. **Requirement**: The formula MUST derive weights from the 'Key Entities' (PsychometricScore) definition in the spec or a cited psychometric source. If a source is unavailable, the task MUST define a placeholder key `DERIVED_WEIGHTS` and raise a `NotImplementedError` at runtime if the weights are not populated by research, rather than inventing arbitrary weights (e.g., 0.6/0.4). The quantitative weights MUST be defined as `Weight_likes = 0.7` and `Weight_sentiment = 0.3` if derived from the Key Entities priority, ensuring compliance with FR-008 and the Single Source of Truth principle.
- [X] T015b [US1] Ensure the measurement model formula defined in T015a is importable and usable by other modules by verifying the import in `code/utils/constants.py` and adding a unit test stub in `tests/unit/test_constants.py` to confirm the formula is accessible. **Dependency**: Sequential after T015a.
- [X] T025a [US3] **Moved from Phase 5**: Ensure `StabilityThresholdViolationError` is defined in `code/utils/exceptions.py` (Task T006b) before it is used in Phase 5. This task confirms the exception exists and is importable. **Dependency**: Sequential after T006b.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition, Validation, and Synthetic Generation (Priority: P1) 🎯 MVP

**Goal**: Successfully load/verify real data or generate synthetic data with known ground truth (SEM-based) ensuring longitudinal match and required columns.

**Independent Test**: The pipeline can be tested by attempting to load the specified dataset (real or synthetic) and checking for the presence of required columns (engagement counts, Rosenberg Self-Esteem Scale scores, comment sentiment scores, and temporal ordering).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009a [P] [US1] Unit test for setting up the SEM model structure in `code/data/generator.py` in `tests/unit/test_generator.py`.
- [X] T009b [P] [US1] Unit test for generating synthetic data with the SEM model in `code/data/generator.py` in `tests/unit/test_generator.py`. <!-- FAILED: unspecified -->
- [X] T009c [P] [US1] Unit test for verifying that synthetic data converges to target SEM parameters in `tests/unit/test_generator.py`.
- [X] T010 [P] [US1] Unit test for `code/data/validator.py` verifying that missing data (N < 100) or missing longitudinal order triggers a specific error in `tests/unit/test_validator.py`.

### Implementation for User Story 1

- [X] T011a [P] [US1] Add `semopy` library to `requirements.txt` and verify installation for SEM implementation.
- [X] T011 [US1] Implement `code/data/generator.py` to create synthetic data using a Structural Equation Model (SEM) via `semopy` that explicitly models measurement error and reverse causality as a **validation mechanism** (not a causal claim), ensuring `device="cpu"` compatibility. <!-- FAILED: unspecified -->
- [X] T011b [US1] Implement verification logic in `code/data/generator.py` to confirm the synthetic data recovers the *observed* association parameters (as defined in the Plan's 'Key Methodological Correction') rather than just the latent causal beta, and log this verification. <!-- FAILED: unspecified -->
- [X] T011c [US1] Implement validation logic in `code/data/generator.py` to ensure the generated synthetic data adheres to RSES psychometric properties (e.g., simulated Cronbach's alpha > 0.7) as required by Constitution Principle VI.
- [X] T015 [US1] Implement `code/data/processor.py` to apply FR-008: Derive 'Perceived Social Validation' from engagement metrics and comment sentiment using the mathematical formula defined in `code/utils/constants.py` (T015a).
- [X] T012 [US1] Implement `code/data/loader.py` to attempt fetching real datasets. **CRITICAL**: Must raise a custom `DataLoadError` with a standardized message format (e.g., "DataLoadError: Failed to fetch real dataset from [URL]") on failure; NO synthetic fallback in the loader itself (fallback handled by orchestration).
- [X] T013 [US1] Implement `code/data/validator.py` to check for: (1) Presence of engagement metrics, sentiment scores, and psychometric scales; (2) Distinct handling: If N=0, raise `DataGapError`; If 0<N<100, raise `InsufficientSampleError`; (3) **Longitudinal ordering**: Verify `engagement_timestamp` < `self_report_timestamp` for each row; if not, raise `LongitudinalMismatchError` to halt execution as required by US-1 Acceptance Scenario 2.
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

- [X] T016 [P] [US2] Unit test for `code/analysis/regression.py` verifying coefficient recovery on synthetic data with known ground truth in `tests/unit/test_regression.py`.
- [X] T017 [P] [US2] Unit test for `code/utils/cautions.py` verifying that a report with "causes" is flagged and rejected in `tests/unit/test_cautions.py`.

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement `code/analysis/regression.py` to fit a multiple linear regression model (Outcome: Self-Perception; Predictors: Engagement, Age, Gender, Offline Relationships, Intrinsic Traits) using `statsmodels`.
- [X] T019 [P] [US2] Implement VIF calculation in `code/analysis/regression.py` to detect multicollinearity for all predictors, returning the calculated VIF values for each predictor.
- [X] T019b [US2] Calculate VIF values for all predictors and compare them against the threshold defined in `code/utils/constants.py`.
- [X] T019d [US2] Write the calculated VIF values, threshold value, and comparison status to `data/processed/model_results_v{timestamp}.json` under a dedicated key `vif_results`. **Schema**: `{"vif_results": {"values": {...}, "threshold": float, "status": "PASS/FAIL"}}`. **Logic**: Do not overwrite existing files; generate a new versioned file for each run. **Crucially**, immediately generate the SHA-256 content hash of this new file and record it in `state/projects/PROJ-447-...yaml` to comply with Constitution Principle V (Versioning Discipline).
- [X] T020 [US2] Implement output formatting in `code/analysis/regression.py` to ensure all findings are labeled "associational". **First, generate a draft report buffer in memory as a JSON string containing a summary of coefficients and p-values**, then run the causal language scanner (imported from `code/utils/cautions.py` defined in T006) on this buffer; **if any trigger word is found, raise `CausalLanguageViolationError` (imported from `code/utils/exceptions.py` defined in T006b) to halt the pipeline (integrated with T028)**.
- [X] T021 [US2] Integrate regression results into `code/main.py` to **append** model coefficients, p-values, confidence intervals to the `data/processed/model_results_v{timestamp}.json` file created by T019d. **Do not overwrite** the existing `vif_results` section; merge with existing VIF data to preserve SC-002 verification. **Schema**: Append a `regression_results` key containing a dict with keys `coefficients`, `p_values`, `ci_lower`, `ci_upper`. **Dependency**: Sequential after T019d.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness, Sensitivity, and Visualization (Priority: P3)

**Goal**: Verify stability against outliers/confounders, check non-linearity, and generate diagnostic plots.

**Independent Test**: The robustness check can be tested by artificially introducing outliers or toggling confounders and verifying the system reports the sensitivity of the results.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Integration test for sensitivity analysis verifying that coefficient variation is calculated correctly across strategies in `tests/integration/test_sensitivity.py`.
- [X] T023 [P] [US3] Unit test for `code/viz/plots.py` verifying that scatter and residual plots are generated and saved to disk in `tests/unit/test_plots.py`.

### Implementation for User Story 3

- [X] T024a [P] [US3] Implement `run_sensitivity_matrix()` function in `code/analysis/sensitivity.py` to re-run the regression with **three outlier strategies ('none', 'IQR removal', 'winsorization') AND with critical confounders included/excluded (creating a matrix of runs)**, reporting the variation in the primary coefficient for each strategy. **Crucially**, this function must calculate the variation in the primary coefficient and **immediately raise `StabilityThresholdViolationError` (imported from `code/utils/exceptions.py` defined in T006b) if the variation exceeds the threshold defined in `code/utils/constants.py` (T005b)**.
- [X] T024b [US3] Implement `save_sensitivity_results()` function in `code/analysis/sensitivity.py` to **save the results of T024a to `data/processed/sensitivity_analysis.json`**. **Schema**: Save a JSON list of results with keys for each strategy's coefficient, p-value, and the calculated variation delta.
- [X] T024c [US3] Implement `verify_sensitivity_matrix()` function in `code/analysis/sensitivity.py` to verify that the `sensitivity_analysis.json` file contains the expected 6 runs (3 strategies x confounder states) and raise an error if not.
- [X] T025a [US3] Implement logic in `code/analysis/sensitivity.py` to **read the data/processed/sensitivity_analysis.json generated by T024b**, calculate the variation in the primary coefficient, **read the stability threshold from `code/utils/constants.py`** (defined in T005b), and **return the variation value**. (Note: The raise logic is now handled in T024a).
- [X] T025b [US3] **Removed**: Logic for raising error is now consolidated in T024a. This task is deprecated.
- [X] T026 [P] [US3] Implement `code/analysis/nonlinearity.py` to fit a quadratic term for the primary predictor and report its significance.
- [X] T027 [US3] Implement `code/viz/plots.py` to generate: (1) Scatter plot with regression line; (2) Residual diagnostic plot; (3) Save as PNG files in `data/processed/` with exact filenames: `scatter_plot.png`, `residuals.png`.
- [X] T027a [US3] Implement logic in `code/main.py` (orchestration) or a dedicated utility to **count the number of generated visualization files** in `data/processed/` **after T027 completes**. **Specifically check for the existence of `scatter_plot.png` and `residuals.png`**. If the count is less than **2** (the mandatory set defined in SC-005), **raise `InsufficientSampleError`** to halt the pipeline. **Dependency**: Sequential after T027. <!-- FAILED: unspecified -->
- [X] T028 [US3] Update `code/main.py` to execute sensitivity and non-linearity checks after the primary model. **Explicitly import and invoke the scanner function from `code/utils/cautions.py`** (defined in T006) and catch `CausalLanguageViolationError` (from T006b/T020), and catch `StabilityThresholdViolationError` (from T006b/T024a), and halt the pipeline immediately if either is raised. Aggregate all results into a final report. **Dependency**: Sequential after T025b (or T024a if T025b is removed).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029a [P] Create `README.md` with project overview, installation instructions, and usage examples.
- [X] T029b [P] Create `quickstart.md` with step-by-step guide to run the pipeline end-to-end.
- [X] T029c [P] Update `README.md` and `quickstart.md` with links to relevant documentation and artifacts.
- [X] T030a [P] Code cleanup and refactoring to ensure type hinting and docstrings; **verify pass with `ruff check` (zero errors)**.
- [X] T030b [P] Code cleanup and refactoring to ensure type hinting and docstrings; **verify pass with `black --check` (zero diffs)**.
- [X] T031 Performance optimization (ensure data processing fits within available system memory constraints); **verify peak memory usage < 6GB during synthetic generation using `memory_profiler` (run `mprof run code/main.py` and inspect output)**.
- [X] T032 [P] Additional unit tests for edge cases (e. g., zero rows, missing demographics) in `tests/unit/`.
- [X] T033 Security hardening: Ensure no PII is written to logs or outputs.
- [X] T034 Run `quickstart.md` validation to ensure end-to-end reproducibility.

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
 - **Execution Flow**: T014 (Orchestrator) calls T012 (Loader). If T012 fails, T014 calls T011 (Generator). T014 then calls T013 (Validator). T015b (Define Model) and T015 (Implement Model) are prerequisites for T014's data processing.
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
Task: "Unit test for setting up the SEM model structure in code/data/generator.py in tests/unit/test_generator.py"
Task: "Unit test for generating synthetic data with the SEM model in code/data/generator.py in tests/unit/test_generator.py"
Task: "Unit test for verifying that synthetic data converges to target SEM parameters in tests/unit/test_generator.py"

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
- **Causal Language**: The `cautions.py` scanner (T006) is mandatory for FR-006; any report containing "causes", "leads to", etc., must trigger `CausalLanguageViolationError` (T020) and halt. T028 must explicitly call this scanner.
- **Stability**: Coefficient variation exceeding the threshold must trigger `StabilityThresholdViolationError` (T024a) and halt (T028). T025a ensures the exception is defined in Phase 2.
- **Measurement Model**: The formula for 'Perceived Social Validation' is defined in `constants.py` (T015a) as a weighted linear combination. **Correction**: The formula weights MUST be derived from the spec or a cited source; if not, a placeholder `DERIVED_WEIGHTS` is used and runtime error raised. **NO arbitrary weights (e.g., 0.6/0.4) are permitted.**
- **SEM Library**: The plan requires `semopy` for SEM implementation; ensure it is installed and used in T011.
- **Sensitivity Analysis**: T024 MUST implement the full 3x2 matrix (outlier strategies x 2 confounder states) to satisfy FR-004. The output must be saved to `sensitivity_analysis.json`.
- **VIF Verification**: T019b, T019c, T019d MUST log the comparison result (value, threshold, status) to satisfy SC-002. T021 appends the rest of the results to the same file without overwriting the VIF section.
- **Exception Handling**: All custom exceptions are defined in `code/utils/exceptions.py` (T006b). T025a ensures `StabilityThresholdViolationError` is available. T013 raises `LongitudinalMismatchError` for invalid timestamps.
- **Visualization Check**: T027a must run after T027 and raise `InsufficientSampleError` if files are missing (count < 2).
- **Versioning**: T019d must write versioned files and record hashes to comply with Constitution Principle V.
