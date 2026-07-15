# Tasks: Statistical Analysis of Publicly Available Sports Data for Predictive Modeling

**Input**: Design documents from `/specs/001-sports-prediction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions
- **Dependencies**: Tasks may list `Depends on: T###` if they require another task's output.

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md`: directories `code/`, `data/raw/`, `data/processed/`, `tests/`, `artifacts/reports/`, `artifacts/figures/`, `state/`
- [ ] T002 Initialize Python 3.10 project with pinned dependencies in `requirements.txt` using command `pip freeze > requirements.txt`. Include: pandas==2.0.3, scikit-learn==1.3.0, xgboost==1.7.6, statsmodels==0.14.0, requests==2.31.0, pyyaml==6.0.1, numpy==1.24.3, pytest==7.4.0
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` for paths, random seeds, and hyperparameters
- [X] T005 [P] Implement `code/checksum_manifest.py` for artifact hashing and state updates
- [ ] T006 [P] Setup `tests/` directory structure with `conftest.py` and fixture mocks for data loading <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->
- [ ] T007 Create base data models in `code/data_models.py` (GameRecord, TeamMetrics, ModelResult)
- [X] T008 Configure error handling and logging infrastructure in `code/utils/logging.py`
- [~] T009 Setup environment configuration management: create `.env.example` file with variables `DATA_PATH`, `RANDOM_SEED`, `CI_MODE`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Data Pipeline and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Implement an automated pipeline that ingests raw data (Retrosheet/BR), handles missing sources with a synthetic fallback, engineers traditional/advanced metrics, and enforces strict temporal splits.

**Independent Test**: The pipeline executes end-to-end on a fresh environment, producing a single CSV with no data leakage between 2000-2018 (train) and 2019-2022 (test), and validates completeness ≥ 95%.

**Dependencies**: T013a/T013b depend on T012a. T014, T015, T016a depend on T013a/T013b.

### Implementation for User Story 1

- [ ] T012a [US1] Implement `code/data_loader.py`: Fetch Retrosheet/BR data. Implement **Data Source Fallback Protocol**: detect 403/429/timeout -> trigger Synthetic Mode -> log status. Output `is_real_data` flag.
- [ ] T012c [US1] Implement `code/data_loader.py`: **Synthetic Generator** logic mimicking MLB distributions (verified against public aggregates). Only executed if T012a triggers fallback.
- [ ] T012b [US1] Implement logic to document 'Synthetic Fallback' status in `artifacts/reports/final_report.json` if Synthetic Mode is triggered, explicitly framing results as 'Validation-Only' to satisfy FR-001 real-data requirement distinction. **Depends on: T012a**
- [X] T013a [US1] **Depends on: T012a**: Implement `code/feature_engineering.py`: Calculate **Traditional Metrics** (AVG, ERA) per game.
- [X] T013b [US1] **Depends on: T012a**: Implement `code/feature_engineering.py`: Calculate **Advanced Metrics** (wOBA, BABIP, park-adjusted run expectancy) per game.
- [X] T014 [US1] **Depends on: T013b**: Implement `code/feature_engineering.py` logic for handling missing advanced metrics (impute with league average for that year or exclude systemic missingness).
- [X] T015 [US1] **Depends on: T013b**: Implement `code/feature_engineering.py` logic for temporal split: Train (≤2018), Test (-2022); handle 2020 pandemic season (exclude or down-weight).
- [~] T016a [US1] **Depends on: T015**: Implement data completeness validation logic (≥95% required variables). **ENFORCEMENT**: RAISE ValueError if rate < 95% AND `is_real_data` is True. Flag 'Empirical Hypothesis Untested' if Synthetic Mode was used.
- [ ] T016b [US1] **Depends on: T016a**: Generate evidence artifact `artifacts/reports/data_completeness_report.json` containing the completeness rate and the 'Empirical Hypothesis Untested' flag if applicable (satisfies SC-005 measurability).
- [ ] T017 [US1] **Depends on: T016b**: Add logging for data ingestion stats, synthetic fallback triggers, and imputation actions.
- [ ] T018 [P] [US1] Write unit tests for wOBA/BABIP calculation formulas in `tests/test_feature_engineering.py`

**Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️**
> **NOTE**: T010 and T011 are **Integration Tests** (not stubs). They require implementation artifacts.
- [ ] T010 [US1] Contract test for data loader output schema in `tests/test_data_loader_schema.py`. **Depends on: T012a**
- [ ] T011 [US1] Integration test for temporal split integrity (no 2019 data in train) in `tests/test_temporal_split.py`. **Depends on: T015**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Model Training and Evaluation (Priority: P2)

**Goal**: Train Logistic Regression, Random Forest, and Gradient Boosting models using time-series cross-validation and compare performance between traditional and advanced feature sets.

**Independent Test**: The training script produces a JSON report with ROC-AUC, log-loss, and Brier scores for both feature sets across all three algorithms, including hyperparameter tuning results.

**Dependencies**: T024 depends on T023a. T025-T028 depend on T024.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️
- [ ] T019 [US2] Contract test for model output JSON schema in `tests/test_model_output_schema.py`. **Depends on: T024**
- [ ] T020 [US2] Integration test for time-series cross-validation split logic in `tests/test_cv_split.py`. **Depends on: T022**

### Implementation for User Story 2

- [ ] T021a [US2] [P] Implement `code/models.py`: Setup **Logistic Regression** wrapper.
- [ ] T021b [US2] [P] Implement `code/models.py`: Setup **Random Forest** wrapper.
- [ ] T021c [US2] [P] Implement `code/models.py`: Setup **Gradient Boosting (XGBoost CPU)** wrapper.
- [ ] T022 [US2] **Depends on: T021a, T021b, T021c**: Implement `code/models.py`: Configure k-fold time-series cross-validation with hyperparameter tuning (GridSearchCV/RandomizedSearchCV).
- [ ] T023a [US2] **Depends on: T022**: Implement `code/models.py`: Train models on two distinct feature sets: "Traditional Metrics" vs "Advanced Metrics".
- [ ] T023b [US2] **Depends on: T023a**: Implement `code/evaluation.py`: Nested Model Comparison logic to isolate marginal gain of advanced metrics due to collinearity (satisfies plan's Complexity Tracking).
- [ ] T024 [US2] **Depends on: T023a**: Implement `code/evaluation.py`: Evaluate all models on the held-out test set (2019-2022).
- [ ] T025 [US2] **Depends on: T024**: Implement `code/evaluation.py`: Calculate ROC-AUC, log-loss, and Brier scores for both feature sets.
- [ ] T026 [US2] **Depends on: T025**: Implement `code/evaluation.py`: Identify and report the specific model/feature combination with the highest ROC-AUC.
- [ ] T027 [US2] **Depends on: T025**: Implement `code/evaluation.py`: Detect and flag "generalization gap" if test ROC-AUC is substantially lower than train ROC-AUC (concrete threshold rule).
- [ ] T028 [US2] **Depends on: T027**: Add logging for hyperparameter search progress and final model selection.
- [ ] T029 [P] [US2] Write unit tests for metric calculations in `tests/test_evaluation_metrics.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Methodological Validation (Priority: P3)

**Goal**: Perform rigorous statistical significance testing (Diebold-Mariano/corrected t-test) and sensitivity analysis to validate findings and frame them as associational.

**Independent Test**: The analysis script produces a report with p-values for paired comparisons, a sensitivity analysis plot/table, and a methodological validity statement.

**Dependencies**: All Phase 5 tasks depend on Phase 4 (US2) completion. T034, T035 depend on T032.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️
- [ ] T030 [US3] Contract test for statistical report schema in `tests/test_statistical_report_schema.py`. **Depends on: T037**
- [ ] T031 [US3] Integration test for sensitivity analysis range sweep in `tests/test_sensitivity_analysis.py`. **Depends on: T034**

### Implementation for User Story 3

- [ ] T032 [US3] **Depends on: Phase 4 Completion**: Implement `code/evaluation.py`: Perform **Diebold-Mariano test OR corrected resampled t-test** (specifically for time-series cross-validation) on cross-validated ROC-AUC scores. **FORBID** standard t-tests.
- [ ] T033 [US3] **Depends on: T032**: Implement `code/evaluation.py`: Calculate p-values and determine significance at α = 0.05.
- [ ] T034 [US3] **Depends on: T032**: Implement `code/evaluation.py`: Execute sensitivity analysis sweeping classification thresholds across the full valid range [0.0, 1.0] with a **step size of 0.01**.
- [ ] T035a [US3] **Depends on: T032**: Define utility function/cost matrix as a concrete artifact `artifacts/config/cost_matrix.json`. Schema: `{"false_positive_cost": 1.0, "true_negative_value": 1.0, "false_negative_cost": 1.0, "true_positive_value": 1.0}`.
- [ ] T035b [US3] **Depends on: T035a**: Implement `code/evaluation.py`: Use cost matrix from T035a to report variance in false-positive/false-negative rates (justifies the analysis).
- [ ] T036 [US3] **Depends on: T035b**: Implement `code/evaluation.py`: Generate sensitivity analysis plot/table and save to `artifacts/figures/`.
- [ ] T037 [US3] **Depends on: T036**: Implement final report generation in `artifacts/reports/final_report.json` with explicit "Associational" framing.
- [ ] T038 [US3] **Depends on: T037**: Add logic to flag results as "Pipeline Validation Only" if Synthetic Mode was triggered in US1.
- [ ] T039 [P] [US3] Write unit tests for statistical test implementations in `tests/test_statistical_tests.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `README.md` and `docs/`
- [ ] T041a [P] Refactor: Extract metric calculation logic into `code/utils/metrics_helper.py` for reusability
- [ ] T041b [P] Refactor: Consolidate logging calls in `code/utils/logging.py` for consistency
- [ ] T042a [P] Performance: Implement early stopping in `code/models.py` for XGBoost to ensure training completes within 6h on 2 vCPU
- [ ] T042b [P] Performance: Add timeout logic in `code/main.py` to enforce a time limit and fail gracefully
- [ ] T043 [P] Additional unit tests coverage checks in `tests/unit/`
- [ ] T044 Security hardening: Add `.gitignore` rules for `.env` files; Implement input validation in `data_loader.py` for data paths.
- [ ] T045 Run `quickstart.md` validation: Execute command `python code/main.py --validate` and verify exit code 0.
- [ ] T046 Execute `checksum_manifest.py` to update `state/` with final artifact hashes

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces the dataset required by US2.**
 - **Internal Order**: T012a -> T012c (conditional) -> T013a/T013b -> T014 -> T015 -> T016a -> T016b -> T017.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1** for the processed dataset.
 - **Internal Order**: T021a/b/c -> T022 -> T023a -> T023b -> T024 -> T025 -> T026 -> T027 -> T028.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US2** for the cross-validated scores and test metrics.
 - **Internal Order**: T032 -> T033 -> T034 -> T035a -> T035b -> T036 -> T037 -> T038.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (TDD-first).
- Data loading (T012a) before Feature Engineering (T013a/b).
- Feature Engineering (T013a/b) before Model Training (T021a/b/c).
- Model Training (T021a/b/c) before Evaluation (T024).
- Evaluation (T024) before Statistical Testing (T032).
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- T021a, T021b, T021c are parallel-safe model definitions.
- Different user stories can be worked on in parallel by different team members (provided data flow is respected).

---

## Parallel Example: User Story 2

```bash
# Launch all model definitions for User Story 2 together:
Task: "Implement code/models.py: Logistic Regression wrapper (T021a)"
Task: "Implement code/models.py: Random Forest wrapper (T021b)"
Task: "Implement code/models.py: Gradient Boosting wrapper (T021c)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data integrity, synthetic fallback logic)
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Modeling) - *Can start once T012a is done*
 - Developer C: User Story 3 (Stats) - *Can start once T024 is done*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except where explicitly noted).
- [Story] label maps task to specific user story for traceability.
- Each user story should be independently completable and testable.
- Verify tests fail before implementing.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.
- **Critical Constraint**: All tasks must run on free CPU-only CI (limited cores, constrained RAM, no GPU). Do not use 8-bit/4-bit quantization or CUDA-specific code.
- **Data Integrity**: Real data is preferred; if synthetic fallback is used, results must be labeled "Pipeline Validation Only" and the empirical hypothesis marked as untested.