# Tasks: Predicting the Impact of Laser Surface Texturing on Wear Resistance

**Input**: Design documents from `/specs/001-predict-lst-wear/`
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

- [ ] T001 Create project structure per implementation plan by executing `mkdir -p code data tests state reports models data/raw data/processed` to create the exact directories: `code/`, `data/`, `tests/`, `state/`, `models/`, `data/raw/`, `data/processed/`, `reports/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement global seed management in `code/seed.py` (set `numpy` and `random` seeds)
- [X] T005 Implement data hygiene utilities in `code/hygiene.py` (MD5 checksum generation, `state/artifact_hashes.yaml` updates)
- [X] T006 Implement environment configuration management by creating `code/config/schema_map.json` defining the canonical column mapping logic (e.g., `{'power': ['laser_power', 'laser_pwr'], 'hardness': ['hv', 'vickers']}`) and examples of source column names to target columns (FR-001), and then implementing the loader to read this JSON file for schema standardization (FR-001); MUST be created before T010.
- [X] T007 Create base data models/entities in `code/models.py` (LSTRecord, ModelPerformance, FeatureImportance)
- [X] T008 Configure error handling and logging infrastructure by creating `code/logging_config.py` to log to `logs/pipeline.log` with level INFO and raise `ValueError` on missing real data (no synthetic fallbacks)
- [ ] T009 Create directories `data/raw/`, `data/processed/`, `models/`, `reports/` and verify their existence
- [ ] T039 [P] Verify `research.md` (defined in Plan Phase 0) contains only verified static URLs/IDs before ingestion (Constitution II); ensure no dynamic search logic is used for data sources; MUST run before T010.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Aggregate and Preprocess LST Wear Data (Priority: P1) 🎯 MVP

**Goal**: Ingest raw tabular data from diverse sources, standardize schema, handle missing values per FR-002/FR-009, and create a clean, analysis-ready dataset.

**Independent Test**: Run ingestion on a mock dataset; verify output CSV has exact canonical columns, no missing predictors, and correct `normalization_method` flags.

### Implementation for User Story 1

- [X] T010 [US1] Implement `code/ingest.py` to fetch data from OpenML, HuggingFace, and literature supplements using specific static IDs/URLs defined in `research.md` (FR-001); fail if `research.md` is missing or IDs are undefined.
- [X] T011 [US1] Implement schema standardization logic in `code/ingest.py` mapping source columns to `pulse_duration`, `power`, `scanning_speed`, `pattern_geometry`, `hardness`, `elastic_modulus`, `wear_rate` using `code/config/schema_map.json` (FR-001); logic MUST iterate through source columns and apply the mapping defined in the JSON file.
- [ ] T012 [US1] Implement missing value handling: DROP records with missing predictors; RETAIN records with missing `contact_load`/`sliding_speed` and set `normalization_method='raw'` (FR-002)
- [X] T013 [US1] Implement Archard's Law normalization in `code/ingest.py` to compute wear coefficient `K`; flag raw records where normalization inputs are missing; EXCLUDE `contact_load` and `sliding_speed` from the predictor feature set when the target is `K` to avoid circular validation (FR-009, Plan Constraints); explicitly distinguish between 'feature exclusion' (column selection) and 'record retention' (row filtering) to ensure records with missing `contact_load`/`sliding_speed` are retained with the `normalization_method='raw'` flag.
- [X] T015 [US1] Generate `data/processed/aggregated_clean.csv` and update `state/artifact_hashes.yaml` with checksums
- [X] T016 [US1] Implement pre-check logic to calculate total record count, split into `normalized_count` and `raw_count`, compare `normalized_count` against the 300 threshold, and trigger a specific `power_limitation` warning if the threshold is not met; write results to `reports/pre_check.json` (SC-004, SC-006); MUST run after T015 and before Phase 4.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Validate Regression Models (Priority: P2)

**Goal**: Train multiple regression models, perform hyperparameter tuning, evaluate performance, and conduct leave-one-material-class-out validation.

**Independent Test**: Execute training pipeline; verify best model (highest R²) is saved, metrics logged, and LOMO transferability failure flags are set correctly.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/train.py` to train Linear Regression, Random Forest, and Gradient Boosting models on CPU only (FR-003); ensure all preprocessing (including one-hot encoding of `pattern_geometry`) is encapsulated within the `Pipeline` to prevent data leakage (Constitution VI); explicitly define the interaction between grid search CV and the held-out test set, specifying that the dataset is split into train/test FIRST, then grid search is performed ONLY on the training split to prevent leakage.
- [ ] T018 [US2] Implement GridSearchCV with at least 10 distinct hyperparameter combinations (n_estimators, max_depth, learning_rate) and 5-fold CV (FR-004); ensure grid search is performed within the training fold of a nested CV or on a separate training split to prevent leakage.
- [ ] T019 [US2] Implement evaluation logic to calculate R², MAE, RMSE and select best model by highest R² (SC-001)
- [X] T020 [US2] Implement custom Leave-One-Material-Class-Out (LOMO) cross-validation splitter in `code/train.py` (FR-006)
- [ ] T021 [US2] Implement LOMO logic to skip classes with < 15 records and fallback to K-Fold if < 3 classes total; log warnings (FR-006)
- [ ] T022 [US2] Implement transferability failure analysis: compute `test_R²_loo / test_R²_standard` ratio; calculate and log the specific drop in R² (defined as standard_test_R2 - lomo_test_R2) as a distinct measurement for SC-003; flag `transferability_failure: true` if ratio < 0.8 (US-2, SC-003)
- [ ] T023 [US2] Implement sensitivity analysis (FR-011) comparing model performance on 'normalized-only' vs 'full' (normalized + raw) subsets; explicitly calculate and report the delta (difference) in R² and MAE between the two subsets; handle the mixed dataset by splitting based on `normalization_method` and running separate models or a unified model with the flag as a feature (FR-011, Plan Summary)
- [ ] T024 [US2] Ensure all scaling and feature engineering (including one-hot encoding) happen inside CV folds using `Pipeline` (Constitution VI); verify no standalone preprocessing steps exist outside the `Pipeline`.
- [ ] T025 [US2] Save `models/best_model.joblib` and `reports/model_performance.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpret Feature Importance and Interactions (Priority: P3)

**Goal**: Extract SHAP values, rank feature importance, visualize interactions, and perform conditional permutation testing.

**Independent Test**: Generate SHAP plots; verify `scanning_speed` and `pattern_geometry` are top contributors; validate conditional permutation p-values.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/interpret.py` to compute SHAP values for the best model (FR-005)
- [ ] T027 [US3] Generate SHAP summary plot (top features) and dependency plots for `power` vs `scanning_speed` (US-3)
- [ ] T028 [US3] Implement logic to detect non-linear interactions (SHAP interaction magnitude > 0.1 or polynomial R² > 0.5) (US-3)
- [ ] T029 [US3] Implement VIF diagnostics in `code/preprocess.py`; drop features with VIF > 5 before permutation tests; MUST run before T030 (FR-010)
- [ ] T030 [US3] Implement conditional permutation testing with a minimum of 500 permutations (increased to 2000 if conditional permutation is used per Plan Phase 3) for feature significance, using orthogonalization or conditional sampling (FR-008, Plan Phase 3); avoid standard permutation on collinear features; align with spec's 'minimum 500' language.
- [ ] T031a [US3] Check for `microstructural_features` column in the dataset; if missing, set `validation_target_unavailable` flag (SC-002)
- [ ] T031b [US3] If `microstructural_features` exists, implement validation logic to compare SHAP rankings against the independent physical mechanism or held-out experimental data; explicitly check for external validation data availability first (via `config/validation.yaml`), and if missing, set `validation_target_unavailable` flag; if internal columns are used, ensure they are truly independent (SC-002).
- [ ] T032 [US3] Generate `reports/interpretation.html` and `reports/vif_report.json`
- [ ] T033 [US3] Implement final report generation in `code/report.py` aggregating all metrics, flags, and associational framing (FR-007)
- [ ] T033b [US3] Implement logic to scan report text for forbidden causal terms (e.g., 'causes', 'determines') and enforce associational framing programmatically before finalizing the report (FR-007)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Implement automated runtime instrumentation to measure pipeline start/stop times, calculate total duration, and fail the run immediately with a non-zero exit code if the 6-hour limit is exceeded (SC-005)
- [ ] T035 [P] Add unit tests for User Stories 1 & 2: Implement `test_ingest_handles_missing_predictors`, `test_preprocess_scaling_leakage`, and `test_train_model_selection` in `tests/unit/` to cover ingestion, preprocessing, and training logic respectively.
- [ ] T036 [P] Add integration test `test_pipeline_flow` in `tests/integration/test_pipeline_flow.py` verifying entry point `code/main.py` produces `data/processed/aggregated_clean.csv` and `models/best_model.joblib`
- [ ] T037a [P] Refactor `code/ingest.py` to reduce cyclomatic complexity < 10
- [ ] T037b [P] Refactor `code/train.py` to remove unused imports and simplify nested loops
- [ ] T038 [P] Update `docs/api.md` with signatures for `code/ingest.py` functions and add `quickstart.md` with installation steps

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - Includes T039 (Research Validation) which MUST run before T010.
 - Includes T006 (Environment Config) which MUST run before T010.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output AND T016 success
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) - Note: T005 and T006 are NOT marked [P] due to dependencies on T001/T004.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for ingestion in tests/contract/test_ingest.py"
Task: "Integration test for preprocessing in tests/integration/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement schema standardization in code/ingest.py"
Task: "Implement missing value handling in code/ingest.py"
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
- **Data Integrity**: Never use synthetic fallbacks; fail loudly if real data fetch fails.
- **Compute**: CPU-only for training; scale down only if GPU is required (not applicable here per FR-003).
- **Critical Ordering**: T039 MUST run before T010. T016 MUST run after T015 and before Phase 4. T029 MUST run before T030. T006 MUST run before T010.