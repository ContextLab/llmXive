# Tasks: The Effects of Gamified Habit Tracking on Long-Term Behavioral Change

**Input**: Design documents from `/specs/001-gamification-effects/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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
  - Delivered as a MVP increment
  
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
- [X] T007 [P] Implement classes `User`, `BehavioralLog`, and `WeeklyAggregation` in `code/data/models.py` with attributes: `user_id` (str), `gamification_status` (bool), `conscientiousness_score` (float), `date` (datetime), `event_type` (str), `week_number` (int), `adherence_flag` (int), matching the Key Entities in spec.md. **Verification**: Assert `import code.data.models` succeeds and class attributes match spec.
- [X] T008 [P] Implement `code/utils/versioning.py` to calculate SHA-256 hashes of artifacts and update `state.yaml` (Constitution Principle V)
- [X] T009 [P] [US1] Setup `contracts/dataset.schema.yaml` defining required columns (User_ID, Gamified, Adherence, Conscientiousness, Need_for_Achievement) and valid tag values for `gamified_app_usage` for validation. **Verification**: Assert file exists and is valid YAML. (FR-001a)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition, Validation, and Aggregation (Priority: P1) 🎯 MVP

**Goal**: Ingest data from a verified longitudinal source (or synthetic generator), validate schema, and aggregate daily logs into weekly bins.

**Independent Test**: The pipeline can be tested by running the data ingestion script on a sample and verifying that the output CSV contains unique user IDs with non-null values for gamification status, weekly adherence counts, and personality scores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (TDD Red), ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test: Add function `test_schema_validation()` in `code/tests/test_ingestion.py` that asserts the ingestion script raises a `ValueError` if `data/consent/` is missing (for real data) or if required columns are absent in the dataset. **Context**: This is a TDD Red task; the script does not exist yet.
- [X] T011 [P] [US1] Integration test: Add function `test_weekly_aggregation()` in `code/tests/test_aggregation.py` that asserts the aggregation script correctly generates `week_number` and `weekly_adherence_flag` columns from raw daily logs. **Context**: This is a TDD Red task; the script does not exist yet.

### Implementation for User Story 1

- [X] T013a [P] [US1] Implement `code/data/synthetic_generator.py`: 
  1. **Primary Path**: Attempt to fetch data from `HABITICA_API_URL` (from env) or load `data/raw/habitica_data.csv`. 
  2. **Fallback**: If ingestion fails (network error, 404, missing credentials, or file not found), generate synthetic data. 
  3. **Synthetic Logic**: Simulate 'self-report' survey. 
     - **Algorithm**: Use `numpy.random.default_rng(seed=42)`. 
     - **Traits**: Generate `conscientiousness_score` ~ N(3.5, 0.8) and `need_for_achievement` ~ N(3.5, 0.8) with correlation 0.6 using Cholesky decomposition. 
 - **Gamification**: Set `gamified_status` = True if reported using gamified apps ([deferred] of users), False otherwise, ensuring ≥30 users are non-gamified.
     - **Logs**: Generate multiple weeks of daily logs per user. 
  4. **Output**: Write to `data/raw/synthetic_data.csv` with columns: `User_ID`, `gamified_status`, `conscientiousness_score`, `need_for_achievement`, `date`, `event_type`. 
  5. **Marker**: If synthetic data is generated, write `data/raw/synthetic_data_marker.json` with `{"source": "synthetic", "n": 100}`. (FR-008, FR-011)
  **Verification**: Assert file exists and contains specified columns. Assert marker file is created if synthetic path is taken.

- [X] T012a [P] [US1] Implement `check_consent()` function in `code/data/validation.py`: 
  1. **First**: Check for `data/raw/synthetic_data_marker.json`. 
  2. **If Absent (Real Data Intended)**: Check for real consent documents in `data/consent/`. If missing, **HALT** with "Data Insufficiency: Missing Consent" error (FR-010, Constitution Principle VI). 
  3. **If Present (Synthetic Data)**: Create `data/consent/synthetic_consent_record.json` (stating data is synthetic) and proceed. 
  4. **If Real Consent Exists**: Proceed. (FR-010)
  **Dependency**: Requires output from T013a (marker file).

- [X] T013b [US1] Implement `code/data/ingestion.py`: 
  1. Check for `data/raw/synthetic_data_marker.json`. 
  2. If present, load `data/raw/synthetic_data.csv`. 
  3. If absent, load `data/raw/habitica_data.csv` (if exists) and validate `gamified_app_usage` tags against `contracts/dataset.schema.yaml`. 
     - **Valid Tags**: Explicitly check for 'gamified', 'points', 'badges'. 
  4. Ensure non-gamified group size ≥ 30 (FR-008). If total valid records < 100 or non-gamified group < 30, log "Data Insufficiency" or "Group Imbalance" and halt. (FR-001, FR-001a, FR-008)

- [X] T014 [US1] Implement `code/data/aggregation.py`: Aggregate daily logs into `week_number` (sequential integers ≥ 1) and `weekly_adherence_flag` (binary 1/0) per user (FR-001b).

- [X] T012b [P] [US1] Implement `calculate_cronbach_alpha()` function in `code/data/validation.py`: Calculate Cronbach's α for personality scales using `pingouin`. Handle missing items by excluding them from the calculation and logging the exclusion count (FR-011). **Dependency**: Requires data from T013b.

- [X] T017 [US1] Generate merged CSV in `data/processed/merged_data.csv` with all required columns (User_ID, Gamified, Adherence, Conscientiousness, Need_for_Achievement). **Verification**: Assert file exists and contains 'User_ID', 'Gamified', 'Adherence', 'Conscientiousness', 'Need_for_Achievement'. If 'Need_for_Achievement' exists, include it; otherwise, log that it was omitted. (FR-001b)
  **Dependency**: Requires output from T014.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Interaction Analysis (Priority: P2)

**Goal**: Fit mixed-effects logistic regression and survival analysis models to predict adherence and dropout.

**Independent Test**: The modeling script can be tested by running it against a synthetic dataset with known interaction coefficients and verifying that the model recovers the interaction term within an acceptable margin of error.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test: Add function `test_model_convergence()` in `code/tests/test_modeling.py` that asserts the mixed-effects model converges and recovers known coefficients within 0.01 variance on a synthetic test set.
- [X] T019 [P] [US2] Integration test: Add function `test_survival_event_count()` in `code/tests/test_survival.py` that asserts the survival analysis halts and outputs descriptive stats if dropout events < 10 per group.

### Implementation for User Story 2

- [X] T021 [US2] Implement VIF calculation and interaction term separation in `code/analysis/modeling.py`: 
  1. **First**, check if `need_for_achievement` column exists. 
  2. If yes, calculate VIF for Conscientiousness and Need for Achievement using `statsmodels.stats.outliers_influence.variance_inflation_factor`. 
  3. If VIF > 5, **drop "Need for Achievement"** (keeping Conscientiousness as primary moderator per Edge Cases), log the removal to `logs/model_fallback.log` with message "Dropped Need for Achievement due to VIF > 5", and proceed. Log that the interaction term was dropped specifically due to collinearity.
  4. If column does not exist, log omission and proceed with Conscientiousness only (FR-002).
  5. **Interaction Term**: Explicitly implement `calculate_interaction_term_na()` function to compute the interaction term between Gamification and Conscientiousness (and Need for Achievement if retained). (FR-002, FR-007)

- [X] T020 [US2] Implement `code/analysis/modeling.py`: Fit mixed-effects logistic regression (fixed effects: Gamification, Conscientiousness, Interaction; random intercepts: User) (FR-002). **Dependency**: Must run after T021 completes.

- [X] T022 [US2] Implement Benjamini-Hochberg (FDR) correction for multiple comparison tests in `code/analysis/modeling.py`. **Scope**: 
  1. Dynamically determine the set of terms to correct: Include `Gamification_x_Conscientiousness` and `Gamification_x_NeedForAchievement` **only if** the corresponding main effects are present in the model. 
  2. **Explicitly EXCLUDE** time points (weeks) and `week_number` from the correction set as they are repeated measures (FR-007). 
  3. Apply correction to the selected set of interaction terms and secondary personality traits. (FR-007)
  **Verification**: Assert the correction list does not contain 'week_number' or temporal indices.

- [X] T023 [US2] Implement Leave-One-User-Out (LOUO) cross-validation in `code/analysis/modeling.py`; report average AUC and variance (US-2 Scenario 3).

- [X] T024 [US2] Implement `code/analysis/survival.py`: Count dropout events (consecutive weeks of non-adherence). If events < 10 per group, **generate a descriptive statistics report** and halt survival analysis (FR-009). If events ≥ 10, proceed to survival analysis.

- [X] T025 [US2] Implement Kaplan-Meier curves and Cox proportional hazards model in `code/analysis/survival.py`, stratified by Conscientiousness quartiles (FR-003).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Validation and Reporting (Priority: P3)

**Goal**: Execute bootstrapping for robustness and generate the final report with visualizations.

**Independent Test**: The validation script can be tested by running the analysis pipeline on a bootstrapped sample and verifying that the generated report includes a section comparing effect sizes across bootstrap iterations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test: Add function `test_bootstrap_variance` in `code/tests/test_robustness.py` that asserts the bootstrapping procedure generates a sufficient number of samples to report a coefficient variance (regardless of value).
- [X] T028 [P] [US3] Integration test: Add function `test_report_generation()` in `code/tests/test_report.py` that asserts the generated report contains Kaplan-Meier curves, sensitivity analysis tables, and the associational disclaimer.

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/analysis/robustness.py`: Execute bootstrapping (sufficient iterations) to generate 95% CI for gamification effect size. **Logic**: 
  1. Use `sklearn.model_selection.StratifiedShuffleSplit` to ensure the ratio of gamified to non-gamified users remains constant (within 5%) across all samples. 
  2. **Report**: Report the coefficient variance across samples and the 95% CI. Compare against SC-004 threshold (0.01) and **flag if variance >= 0.01** (do not silently pass). (FR-004, SC-004)
 **Verification**: Assert [deferred] samples were generated. Assert variance check is performed and reported.

- [X] T031 [US3] Implement sensitivity analysis in `code/reports/generate_report.py`: Vary adherence thresholds over the set **[0.5, 0.6, 0.7, 0.8]** and **calculate/report the stability of the effect size (coefficient variance)** across these specific thresholds (FR-005, SC-005).
  **Verification**: Assert the analysis iterates exactly over [0.5, 0.6, 0.7, 0.8].

- [X] T030 [US3] Implement `code/reports/generate_report.py`: Generate HTML/PDF report containing usage trajectory plots, Kaplan-Meier survival curves, and sensitivity analysis tables. **Inject a header disclaimer programmatically**: "Findings are associational, not causal. The data is observational." (FR-005, FR-006).

- [X] T032 [US3] Generate final report artifact `data/reports/final_analysis.html` by executing `code/reports/generate_report.py`. **Requirements**: 
  1. Include a "Data Limitations" section explicitly stating: "Sample size (N=100), synthetic nature of data, lack of external validation, and potential underpowering for interaction effects." 
  2. Verify file exists and contains required sections. (FR-005, FR-006)
  **Verification**: Assert file exists and contains the "Data Limitations" section with the specified text.

- [X] T033 [US3] Run `code/utils/versioning.py` to hash all final artifacts and update `state.yaml` (Constitution Principle V).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates: Update `README.md` with project overview and `quickstart.md` with execution instructions. **Specifics**: Ensure `quickstart.md` includes steps for synthetic data generation and consent verification.
- [X] T035 [P] Refactor `code/analysis/robustness.py` to use **chunked processing or generator-based iteration** to ensure peak memory usage remains within acceptable limits during bootstrapping, verified by a **memory profiling test**.
- [X] T036 [P] Optimize `code/analysis/robustness.py` by implementing **multiprocessing** for a sufficient number of bootstrap iterations to reduce runtime on CPU-only CI to < 30 minutes.
- [X] T037 [P] Additional unit tests for edge cases: Implement `code/tests/test_edge_cases.py` with functions `test_vif_high_collinearity` (verifies VIF > 5 handling) and `test_low_event_count` (verifies survival halt logic).
- [X] T038 [US3] Run quickstart.md validation: Execute `bash quickstart.sh`, assert exit code 0, verify `data/processed/merged_data.csv` exists, and run pre-flight dependency checks. **Pre-flight Check**: Assert that all dependency files (T009, T013a, T014) exist before execution. (FR-001b, US-1)
  **Verification**: Assert exit code 0 and `data/processed/merged_data.csv` exists.

- [X] T039 [P] [Resolved] Data Flow Correction: Logic merged into T013a and T012a. No separate task required.
- [X] T040 [P] [Resolved] Task Specificity: Merged into T021. No separate task required.
- [X] T041 [P] [Resolved] Stratified Bootstrapping: Merged into T029. No separate task required.
- [X] T042 [P] [Resolved] Report Completeness: Merged into T032. No separate task required.
- [X] T043 [P] Pre-flight Check Implementation: Implement `code/utils/preflight.py` to validate the dependency graph and artifact existence before pipeline execution. **Logic**: Check for required files (T009, T013a, T014) and exit with code 1 if missing. (FR-001b, Constitution V)

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