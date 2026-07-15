# Tasks: Predicting the Influence of Alloying on the Seebeck Coefficient Using Public Data

**Input**: Design documents from `/specs/001-predicting-seebeck-alloying/`
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

- [X] T001a [P] Create directory structure: `projects/PROJ-374-predicting-the-influence-of-alloying-on-/` (code/, data/raw/, data/processed/, docs/figures/, state/)
- [X] T001b [P] Create empty `__init__.py` files in `code/` and `code/utils/` directories

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002a [P] Create `code/requirements.txt` with pinned versions: pandas, scikit-learn, mendeleev, matplotlib, requests, pyyaml, numpy, pytest
- [X] T002b [P] Create `pyproject.toml` or `setup.cfg` for project metadata
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 Create `code/utils/periodic_data.py` wrapper for `mendeleev` periodic table lookups
- [X] T005 Create `code/utils/stoichiometry_parser.py` for formula parsing and normalization
- [X] T006 Create `code/utils/checksums.py` for data hygiene utilities
- [X] T007 Create `code/utils/mapping.json` with schema `{formula: family}` covering Bi-Te, Pb-Te, and Skutterudites
- [ ] T008 Setup `data/raw/` and `data/processed/` directory structure
- [ ] T009 Setup `docs/figures/` directory
- [ ] T010 Setup `state/` directory and initial `state/projects/PROJ-374-predicting-the-influence-of-alloying-on-.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Compositional Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Download the electronic transport database, filter for thermoelectric families, and engineer compositional descriptors.

**Independent Test**: Execute the data pipeline script and verify that the output CSV contains the expected number of rows, no null values in the engineered feature columns, and that calculated feature values match manual calculations for a known sample material.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/01_ingest_and_clean.py`: Download data from DOI 10.1038/sdata.2017.85, parse to DataFrame, save to `data/processed/cleaned_compositions.csv` (verify row count > 0)
- [ ] T012 [US1] Implement filtering logic in `code/01_ingest_and_clean.py`: Retain only Bi-Te, Pb-Te, Skutterudites; exclude missing Seebeck/Composition
- [ ] T013 [US1] Implement stoichiometry mapping in `code/01_ingest_and_clean.py`: Use `utils/mapping.json` to assign material families
- [X] T014 [US1] Implement retention check in `code/01_ingest_and_clean.py`: Calculate retention rate of **filtered input records**; if < 95%, exit with code 1, print "CRITICAL: Retention < 95%" to stderr, and write `state/retention_log.json` with structure: `{"retention_rate": float, "total_input": int, "retained_count": int, "status": "FAIL"}`; otherwise log `{"status": "PASS"}` (verify log contains `status: PASS` for pipeline to continue)
- [X] T015 [US1] Implement `code/02_engineer_features.py`: Calculate Mean Atomic Radius (weighted avg) using `mendeleev`
- [X] T016 [US1] Implement `code/02_engineer_features.py`: Calculate Electronegativity Variance using `mendeleev`
- [X] T017 [US1] Implement `code/02_engineer_features.py`: Calculate Valence Electron Concentration (VEC) (weighted avg)
- [X] T018 [US1] Implement `code/02_engineer_features.py`: Calculate Atomic Number Variance
- [X] T019 [US1] Implement `code/02_engineer_features.py`: Add Temperature as a covariate and Material Family as categorical feature
- [ ] T020 [US1] Save final engineered dataset to `data/processed/final_features.csv` (verify file exists, contains expected columns: mean_atomic_radius, electronegativity_variance, vec, atomic_number_variance, temperature, material_family, and has no nulls in engineered feature columns)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently
**⚠️ Dependency**: Phase 4 (US2) tasks require successful completion of T014 (retention check). If T014 halts, US2 cannot proceed.

---

## Phase 4: User Story 2 - Predictive Modeling and Feature Importance Analysis (Priority: P2)

**Goal**: Train a gradient boosting regressor with CV, evaluate performance, and extract feature importance/correlations.

**Independent Test**: Run the training script and verify that the model achieves an R² score, that the cross-validation loop completes without error, that a 95% confidence interval is reported, and that a ranked list of feature importances and individual correlations is generated.

### Implementation for User Story 2

- [~] T021 [US2] Implement `code/03_train_and_evaluate.py`: Load `data/processed/final_features.csv` (Depends on T020)
- [~] T022 [US2] Implement split logic: If N >= 100, use 80/20 Stratified Split. If N < 100, use Repeated 5-Fold CV (10 repeats) on the full dataset. **Do NOT halt for N < 50**; the Repeated CV fallback is mandatory for small datasets. (Depends on T021)
- [~] T023 [US2] Implement Baseline: Linear Regression model and evaluation
- [~] T024 [US2] Implement Model: `GradientBoostingRegressor` (n_estimators=100, max_depth=3, random_state=42)
- [~] T025 [US2] Implement K-Fold Cross-Validation loop (5-fold) to calculate mean R² and **save individual fold R² scores** to `state/cv_fold_scores.json` for traceability (used for CI in T026b)
- [~] T026a [US2] Implement Permutation Test (A sufficient number of iterations, random_state=42) to calculate p-value for R² significance (null hypothesis: R² = 0). **Note**: Do NOT derive CI from this distribution. (Independent of T026b) <!-- FAILED: unspecified -->
- [~] T026b [US2] Calculate 95% Confidence Interval for R² score derived strictly from the CV fold scores saved in T025 (T025) as required by FR-008. **Note**: Do NOT use permutation distribution for CI. (Independent of T026a)
- [~] T027 [US2] Implement F-test comparison between Gradient Boosting and Linear Regression to verify statistically significant improvement (p < 0.05) over baseline (SC-002, SC-003). **Output**: F-statistic and p-value. Requires T023, T024, T025 completion.
- [~] T028 [US2] Extract and rank top 5 feature importances from the trained model
- [~] T029 [US2] Calculate individual Pearson correlation coefficients (r) for each descriptor vs. Seebeck
- [ ] T030 [US2] Save model metrics, feature importances, and correlations to `data/processed/model_output.json` (verify JSON contains keys: r2_score, ci_lower, ci_upper, p_value, f_statistic, f_p_value, feature_importances)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting of Composition-Property Relationships (Priority: P3)

**Goal**: Generate visualizations of top descriptors vs. Seebeck and produce a summary report with classification.

**Independent Test**: Run the reporting script and verify that output images (PNG/SVG) exist with valid axes labels, and that the text report contains the calculated R², its classification (Success/Inconclusive/Failure), and the 95% confidence interval.

### Implementation for User Story 3

- [~] T031 [US3] Implement `code/04_visualize_and_report.py`: Load model output and features. If `data/processed/model_output.json` is missing or invalid, halt with error.
- [~] T032 [US3] Implement VIF calculation and Pearson correlation matrix for collinearity check
- [~] T033 [US3] Generate scatter plots of Top 3 descriptors vs. Seebeck (with trend lines) to `docs/figures/`
- [~] T034 [US3] Implement Classification Logic: **Success** if R² > 0.2 (regardless of p-value); **Inconclusive** if 0.2 ≤ R² < 0.4; **Failure** if R² < 0.2. Additionally, report a separate "Significance" flag: "Significant" if p < 0.05, else "Not Significant". (Matches spec.md:US-3)
- [ ] T035 [US3] Generate `docs/report.md` containing R², CI, p-value, F-test results, classification (Success/Inconclusive/Failure), and top descriptors (verify report contains R² value, classification string, and 95% CI text)
- [~] T036 [US3] Update root `README.md` with links to figures and summary of findings

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037a [P] Write unit test `test_mean_atomic_radius()` in `code/tests/test_feature_engineering.py`: Test with valid formula, empty formula (expect error/NaN), and single element (expect mean = element radius).
- [X] T037b [P] Write unit test `test_electronegativity_variance()` in `code/tests/test_feature_engineering.py`: Test with valid formula, uniform composition (expect 0 variance), and missing element (expect error/NaN).
- [X] T037c [P] Write unit test `test_vec_calculation()` in `code/tests/test_feature_engineering.py`: Test with valid formula, known VEC value, and empty formula.
- [X] T038 [P] Write unit tests in `code/tests/test_stoichiometry.py` for formula parsing (e.g., "Bi2Te3" -> {"Bi": 2, "Te": 3}, invalid formulas).
- [X] T039 [P] Write unit tests in `code/tests/test_model_metrics.py` for CV and permutation logic (verify CI calculation from fold scores, verify permutation p-value logic).
- [~] T040 Run quickstart.md validation and ensure full pipeline runs within 6 hours on CPU-only runner

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Explicitly depends on successful completion of T014** (retention check) and T020 (final_features.csv).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (`model_output.json`)

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
# Launch all models for User Story 1 together:
Task: "Create `code/utils/periodic_data.py` wrapper for `mendeleev` periodic table lookups"
Task: "Create `code/utils/stoichiometry_parser.py` for formula parsing and normalization"
Task: "Create `code/utils/checksums.py` for data hygiene utilities"
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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Modeling) - *Must wait for US1 data*
 - Developer C: User Story 3 (Reporting) - *Must wait for US2 results*
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