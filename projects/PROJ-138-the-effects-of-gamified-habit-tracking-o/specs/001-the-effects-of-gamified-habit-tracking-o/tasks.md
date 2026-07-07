# Tasks: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

**Input**: Design documents from `/specs/001-gamification-effects/`
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

- [X] T001 Create project structure: Create the following directories at repository root: `code/data`, `code/analysis`, `code/reports`, `code/utils`, `code/tests`, `data/raw`, `data/processed`, `data/consent`. **Verification**: Assert all directories exist and create `.gitkeep` files in each to ensure they are tracked by git.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T002 [P] Initialize Python 3.11 project with requirements.txt dependencies (pandas, numpy, scikit-learn, statsmodels, lifelines, seaborn, matplotlib, pyyaml, pingouin, scipy)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools
- [X] T004 [P] Setup directory structure: `data/raw/`, `data/processed/`, `data/consent/`, `code/data/`, `code/analysis/`, `code/reports/`, `code/utils/`, `code/tests/`
- [X] T005 [P] Implement `code/utils/config.py` for random seed pinning and environment configuration
- [X] T006 [P] Setup `code/utils/logging.py` for structured logging of pipeline stages
- [ ] T007 [P] Implement classes `User`, `BehavioralLog`, and `WeeklyAggregation` in `code/data/models.py` with attributes: `user_id` (str), `gamification_status` (bool), `conscientiousness_score` (float), `date` (datetime), `event_type` (str), `week_number` (int), `adherence_flag` (int), matching the Key Entities in spec.md. **Verification**: Assert `import code.data.models` succeeds and class attributes match spec.
- [X] T008 [P] Implement `code/utils/versioning.py` to calculate SHA-256 hashes of artifacts and update `state.yaml` (Constitution Principle V)
- [ ] T009 [P] Setup `contracts/dataset.schema.yaml` defining required columns (User_ID, Gamified, Adherence, etc.) for validation
- [~] T012a [P] [US1] Implement `check_consent()` function in `code/data/validation.py`: Verify `data/consent/` exists. **Logic**: If real data is present, halt if missing (FR-010). If synthetic data is used, **generate a synthetic consent artifact** (e.g., `data/consent/synthetic_consent_record.json`) explicitly stating the data is synthetic and approved for research, then proceed. This ensures the gate is never bypassed silently. (FR-010, Constitution Principle VI)
- [~] T013a [P] [US1] Implement `code/data/synthetic_generator.py`: Generate a dataset with N=100 users. **Mechanism**: Simulate a 'self-report' survey response for each user to determine `gamified_status` (True if they reported using gamified apps, False otherwise), ensuring at least 30 users are `gamified_status=False` (non-gamified) and 70 are `True` (gamified). Include `conscientiousness_score` and `need_for_achievement` (simulated with known correlation). Pin random seed to a fixed value. **Output**: Write to `data/raw/synthetic_data.csv` in CSV format. (FR-008, FR-011) <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition, Validation, and Aggregation (Priority: P1) 🎯 MVP

**Goal**: Ingest data from a verified longitudinal source (or synthetic generator), validate schema, and aggregate daily logs into weekly bins.

**Independent Test**: The pipeline can be tested by running the data ingestion script on a sample and verifying that the output CSV contains unique user IDs with non-null values for gamification status, weekly adherence counts, and personality scores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (TDD Red), ensure they FAIL before implementation**

- [~] T010 [P] [US1] Contract test: Add function `test_schema_validation()` in `code/tests/test_ingestion.py` that asserts the ingestion script raises a `ValueError` if `data/consent/` is missing (for real data) or if required columns are absent in the dataset. **Context**: This is a TDD Red task; the script does not exist yet.
- [~] T011 [P] [US1] Integration test: Add function `test_weekly_aggregation()` in `code/tests/test_aggregation.py` that asserts the aggregation script correctly generates `week_number` and `weekly_adherence_flag` columns from raw daily logs. **Context**: This is a TDD Red task; the script does not exist yet.

### Implementation for User Story 1

- [~] T012b [P] [US1] Implement `calculate_cronbach_alpha()` function in `code/data/validation.py`: Calculate Cronbach's α for personality scales using `pingouin`. Handle missing items by excluding them from the calculation and logging the exclusion count (FR-011). **Dependency**: Requires data from T013b.
- [~] T013b [US1] Implement `code/data/ingestion.py`: If `data/raw/habitica_data.csv` exists, load it and validate `gamified_app_usage` tags (FR-001a). Otherwise, execute `code/data/synthetic_generator.py` (T013a) with seed=42. Validate `gamified_app_usage` tags per FR-001a. Ensure non-gamified group size ≥ 30 (FR-008) by checking the output of T013a. If total valid records < 100 or non-gamified group < 30, log "Data Insufficiency" or "Group Imbalance" and halt.
- [~] T014 [US1] Implement `code/data/aggregation.py`: Aggregate daily logs into `week_number` (sequential integers ≥ 1) and `weekly_adherence_flag` (binary 1/0) per user (FR-001b).
- [~] T017 [US1] Generate merged CSV in `data/processed/merged_data.csv` with all required columns (User_ID, Gamified, Adherence, Personality Scores). **Verification**: Assert file exists and contains expected columns.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Interaction Analysis (Priority: P2)

**Goal**: Fit mixed-effects logistic regression and survival analysis models to predict adherence and dropout.

**Independent Test**: The modeling script can be tested by running it against a synthetic dataset with known interaction coefficients and verifying that the model recovers the interaction term within an acceptable margin of error.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [P] [US2] Contract test: Add function `test_model_convergence()` in `code/tests/test_modeling.py` that asserts the mixed-effects model converges and recovers known coefficients within 0.01 variance on a synthetic test set.
- [~] T019 [P] [US2] Integration test: Add function `test_survival_event_count()` in `code/tests/test_survival.py` that asserts the survival analysis halts and outputs descriptive stats if dropout events < 10 per group.

### Implementation for User Story 2

- [~] T021 [US2] Implement VIF calculation in `code/analysis/modeling.py`: **First**, check if the `need_for_achievement` column exists in the dataset. If it does, calculate VIF for Conscientiousness and Need for Achievement. If VIF > 5, **drop "Need for Achievement"** (keeping Conscientiousness as primary moderator per Edge Cases) and log the removal. If the column does not exist, log the omission and proceed with Conscientiousness only (FR-002).
- [~] T021b [US2] Implement fallback model logic in `code/analysis/modeling.py`: If both traits are removed or the interaction term is undefined, re-run the model with only Conscientiousness as a fixed effect. **Output**: Log the structural change to `logs/model_fallback.log`. <!-- FAILED: unspecified -->
- [~] T020 [US2] Implement `code/analysis/modeling.py`: Fit mixed-effects logistic regression (fixed effects: Gamification, Conscientiousness, Interaction; random intercepts: User) (FR-002). **Dependency**: Must run after T021 completes.
- [~] T022 [US2] Implement Benjamini-Hochberg (FDR) correction for multiple comparison tests. **Scope**: Apply correction strictly to the set of interaction terms and secondary personality traits (e.g., Need for Achievement interaction). Main effects (Gamification, Conscientiousness) are reported uncorrected unless they are part of the multiple comparison set defined in FR-007 (FR-007).
- [~] T023 [US2] Implement Leave-One-User-Out (LOUO) cross-validation in `code/analysis/modeling.py`; report average AUC and variance (US-2 Scenario 3).
- [~] T024 [US2] Implement `code/analysis/survival.py`: Count dropout events (consecutive weeks of non-adherence). If events < 10 per group, **generate a descriptive statistics report** and halt survival analysis (FR-009). If events ≥ 10, proceed to survival analysis.
- [~] T025 [US2] Implement Kaplan-Meier curves and Cox proportional hazards model in `code/analysis/survival.py`, stratified by Conscientiousness quartiles (FR-003).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Validation and Reporting (Priority: P3)

**Goal**: Execute bootstrapping for robustness and generate the final report with visualizations.

**Independent Test**: The validation script can be tested by running the analysis pipeline on a bootstrapped sample and verifying that the generated report includes a section comparing effect sizes across bootstrap iterations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T027 [P] [US3] Contract test: Add function `test_bootstrap_variance` in `code/tests/test_robustness.py` that asserts the bootstrapping procedure generates [deferred] samples and reports a coefficient variance (regardless of value).
- [~] T028 [P] [US3] Integration test: Add function `test_report_generation()` in `code/tests/test_report.py` that asserts the generated report contains Kaplan-Meier curves, sensitivity analysis tables, and the associational disclaimer.

### Implementation for User Story 3

- [~] T029 [P] [US3] Implement `code/analysis/robustness.py`: Execute bootstrapping (sufficient iterations) to generate 95% CI for gamification effect size. **Output**: Report the coefficient variance across samples and the 95% CI. **Note**: Do not fail if variance > 0.01; report the value as part of the exploratory findings (FR-004, SC-004).
- [~] T031 [US3] Implement sensitivity analysis in `code/reports/generate_report.py`: Vary adherence thresholds and **calculate/report the stability of the effect size (coefficient variance)** across thresholds (FR-005, SC-005).
- [~] T030 [US3] Implement `code/reports/generate_report.py`: Generate HTML/PDF report containing usage trajectory plots, Kaplan-Meier survival curves, and sensitivity analysis tables. **Inject a header disclaimer programmatically**: "Findings are associational, not causal. The data is observational." (FR-005, FR-006).
- [~] T032 [US3] Generate final report artifact `data/reports/final_analysis.html` by executing `code/reports/generate_report.py`. **Verification**: Assert file exists and contains required sections.
- [~] T033 [US3] Run `code/utils/versioning.py` to hash all final artifacts and update `state.yaml` (Constitution Principle V).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T034 [P] Documentation updates: Update `README.md` with project overview and `quickstart.md` with execution instructions. **Specifics**: Ensure `quickstart.md` includes steps for synthetic data generation and consent verification.
- [ ] T035 [P] Refactor `code/analysis/robustness.py` to use **chunked processing or generator-based iteration** to ensure peak memory usage remains within acceptable limits during bootstrapping, verified by a **memory profiling test**.
- [ ] T036 [P] Optimize `code/analysis/robustness.py` by implementing **multiprocessing** for a sufficient number of bootstrap iterations to reduce runtime on CPU-only CI to < 30 minutes.
- [ ] T037 [P] Additional unit tests for edge cases: Implement `code/tests/test_edge_cases.py` with functions `test_vif_high_collinearity` (verifies VIF > 5 handling) and `test_low_event_count` (verifies survival halt logic).
- [ ] T038 Run quickstart.md validation: Execute `bash quickstart.sh`, assert exit code 0, and verify `data/processed/merged_data.csv` exists.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on aggregated data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model outputs from US2

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
Task: "Contract test for data ingestion schema validation in code/tests/test_ingestion.py"
Task: "Integration test for weekly aggregation logic in code/tests/test_aggregation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/validation.py"
Task: "Implement code/data/ingestion.py"
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
- **Constraint**: All tasks must run on CPU-only CI (limited cores, limited RAM). No GPU models or 8-bit quantization allowed.