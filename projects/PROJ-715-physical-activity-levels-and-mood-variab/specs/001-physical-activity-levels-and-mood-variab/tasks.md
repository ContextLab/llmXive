# Tasks: Physical Activity Levels and Mood Variability in Daily Life

**Input**: Design documents from `/specs/001-physical-activity-mood-variability/`
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

- [X] T001a Create `code/__init__.py`
- [ ] T001b Create `data/raw/.gitkeep`, `data/processed/.gitkeep`, and `data/interim/.gitkeep`
- [ ] T001c Create `tests/unit/.gitkeep` and `tests/contract/.gitkeep`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python project with dependencies (`pandas`, `statsmodels`, `scikit-learn`, `pyyaml`, `requests`, `numpy`) in `code/requirements.txt`
- [ ] T003 [P] Configure linting (flake8) and formatting (black) tools in `code/`
- [X] T004 [P] Create configuration module `code/config.py` defining paths, random seeds (a fixed value), constants (including `MISSINGNESS_THRESHOLD`), and the specific OSF DOI string for the dataset
- [~] T005 [P] Create schema definitions in `specs/001-physical-activity-mood-variability/contracts/`: `daily_aggregates.schema.yaml` and `model_results.schema.yaml`
- [~] T006 [P] Create base test utilities in `tests/conftest.py` for schema validation and fixture data
- [~] T007 Implement `code/ingest.py` to download StudentLife dataset from OSF DOI `/...` (specific DOI string from config), verify cryptographic checksum, and convert to `data/raw/bronze.parquet`
- [~] T008 Implement error handling for missing/corrupted files in `code/ingest.py` to fail gracefully with clear error messages

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download StudentLife dataset, parse raw step logs, align EMA mood timestamps, and compute daily aggregates (`total_steps`, `mean_mood`, `mood_std`) per participant-day.

**Independent Test**: Verify that `data/processed/daily_aggregates.csv` contains one row per participant per day with non-null `total_steps`, `mean_mood`, `mood_std`, and row count matches valid participant-days.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Contract test for `daily_aggregates.csv` schema in `tests/contract/test_daily_aggregates.py`
- [~] T010 [P] [US1] Unit test for aggregation logic (handling missing ratings, zero steps) in `tests/unit/test_preprocess_aggregation.py`

### Implementation for User Story 1

- [~] T011 [US1] Implement `code/preprocess.py` to load `data/raw/bronze.parquet` and parse raw step logs into daily totals
- [~] T012 [US1] [Depends: T007] Implement `code/preprocess.py` logic to derive `sleep_duration` and `baseline_affect` from raw data if missing, using `config.MISSINGNESS_THRESHOLD` to decide between derivation and proceeding without them (per spec Assumptions); ensure derived columns are written to the output CSV
- [~] T013 [US1] [Depends: T011] Implement `code/preprocess.py` logic to align EMA mood timestamps and exclude records with missing critical values
- [~] T014 [US1] [Depends: T011] Implement `code/preprocess.py` logic to compute daily aggregates: `mean_mood` and `mood_std` (excluding days with < 2 valid ratings)
- [~] T015a [US1] [Depends: T011] Implement `code/preprocess.py` logic to handle days with zero steps: record `total_steps` as 0 (not null) to preserve the day for analysis
- [~] T015b [US1] [Depends: T014] Implement `code/preprocess.py` logic to handle days with exactly 0 mood variability: apply log-transformation with a small epsilon offset to stabilize variance and handle zero values to the value *before* writing to `daily_aggregates.csv` to ensure the CSV contains the transformed outcome variable
- [~] T016 [US1] Write final output to `data/processed/daily_aggregates.csv` and validate against `daily_aggregates.schema.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Testing (Priority: P2)

**Goal**: Fit linear mixed-effects models to test association between `total_steps` and (a) `mood_std` (log-transformed) and (b) `mean_mood`, controlling for sleep, day-of-week, and baseline affect.

**Independent Test**: Run model fitting script and verify output report contains fixed-effect coefficient for `total_steps` (with p-value and 95% CI) for both models, and model converges successfully.

### Tests for User Story 2

- [ ] T017 [P] [US2] Contract test for `model_results.json` schema in `tests/contract/test_model_results.py`
- [ ] T018 [P] [US2] Unit test for model convergence and coefficient extraction in `tests/unit/test_analysis_modeling.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/analysis.py` to fit LMM with `log(mood_std + 0.01)` (read directly from the pre-transformed column in `daily_aggregates.csv`) as outcome and `total_steps` as predictor (random intercepts for participant)
- [ ] T020 [US2] Implement `code/analysis.py` to fit LMM with `mean_mood` as outcome and `total_steps` as predictor, ensuring the results are included in the final report with equal prominence to the variability model (no 'secondary' classification)
- [ ] T021 [US2] Implement `code/analysis.py` to include covariates (sleep duration, day-of-week, baseline_affect) from `daily_aggregates.csv` in both models
- [ ] T022 [US2] Implement `code/analysis.py` to extract fixed-effect coefficients, standard errors, p-values, and 95% CIs for `total_steps` and covariates
- [ ] T023 [US2] Implement `code/analysis.py` to perform model diagnostics (Shapiro-Wilk, Breusch-Pagan) and generate residual plots (specifically 'residuals vs. fitted')
- [ ] T024 [US2] Implement `code/analysis.py` to ensure all results are explicitly labeled as "associational" in internal data structures
- [ ] T025 [US2] Save model results to `data/processed/model_results.json` and validate against `model_results.schema.yaml`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform leave-one-participant-out (LOPO) cross-validation and sensitivity analyses (weekdays-only, alternative metrics, single-rating handling) to ensure robustness.

**Independent Test**: Verify final report contains LOPO coefficient consistency (≥90% sign stability), sensitivity check results, and bootstrap consistency for single-rating handling (≥80%).

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for LOPO loop logic and coefficient aggregation in `tests/unit/test_analysis_validation.py`
- [ ] T027 [P] [US3] Unit test for sensitivity analysis logic (weekdays filter, metric swap) in `tests/unit/test_analysis_sensitivity.py`

### Implementation for User Story 3

- [ ] T028a [US3] Implement `code/analysis.py` LOPO loop: retrain model N times (N=participants), track `total_steps` coefficient sign stability
- [ ] T028b [US3] Implement `code/analysis.py` logic to calculate the percentage of folds where the `total_steps` coefficient sign matches, flag the result in `model_results.json` if <90%, and **continue execution** (do not raise an error) to allow report generation
- [ ] T029 [US3] Implement `code/analysis.py` sensitivity analysis: re-run primary model on "weekdays only" dataset and compare coefficients
- [ ] T030 [US3] Implement `code/analysis.py` sensitivity analysis: re-run model using "active minutes" instead of step counts and compare direction of effect
- [ ] T031a [US3] Implement `code/analysis.py` logic to exclude single-rating days from the dataset for the primary sensitivity branch
- [ ] T031b [US3] Implement `code/analysis.py` logic to impute single-rating days using the participant's median mood value for the secondary sensitivity branch
- [ ] T031c [US3] Implement `code/analysis.py` to execute a bootstrap sampling loop (1000 iterations, seed 42): for each iteration, fit the exclusion model (T031a logic) and the imputation model (T031b logic), **compare the coefficients of the two models within the iteration**, record whether the direction remains consistent, and verify the consistency of this comparison in ≥80% of the bootstrap samples
- [ ] T032 [US3] Implement `code/report.py` to generate PDF/HTML report containing effect sizes, CIs, diagnostic plots (including 'residuals vs. fitted' from T023), LOPO results, and sensitivity analysis summaries
- [ ] T033 [US3] Ensure report explicitly states "associational" findings and avoids causal language

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034a [P] Update `README.md` with specific sections: Installation, Usage, and Data Description
- [ ] T034b [P] Update `docs/` with specific content: API documentation for `analysis.py` and Data Dictionary for `daily_aggregates.csv`
- [ ] T036 Run full pipeline integration test in `tests/integration/test_full_pipeline.py` to verify end-to-end execution within 6 hours
- [ ] T037 [P] Additional unit tests for edge cases (single participant days, zero variability) in `tests/unit/`
- [ ] T038 Run `quickstart.md` validation to ensure all documentation is accurate

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data output from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model output from US2

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
Task: "Contract test for daily_aggregates.csv schema in tests/contract/test_daily_aggregates.py"
Task: "Unit test for aggregation logic in tests/unit/test_preprocess_aggregation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/preprocess.py to load data and parse step logs"
Task: "Implement code/preprocess.py logic to align EMA timestamps"
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