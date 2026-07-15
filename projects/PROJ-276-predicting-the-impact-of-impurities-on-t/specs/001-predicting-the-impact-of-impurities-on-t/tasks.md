# Tasks: Predicting the Impact of Impurities on the Superconductivity of Magnesium Diboride

**Input**: Design documents from `/specs/001-impurity-impact-mgb2/`
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

## Phase 0: Pre-Flight & Contradiction Resolution

**Purpose**: Address critical spec contradictions before implementation begins

- [ ] T000 [P] **CRITICAL**: Document Spec Contradiction (FR-006 vs Constitution Principle VII). Create `state/contradictions/FR-006-runtime-bug.md` noting the 6-hour spec requirement vs 30-minute Constitution limit. Enforce a time limit in all subsequent tasks.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan. Execute: `mkdir -p src/ingestion src/modeling src/visualization src/utils tests/contract tests/integration tests/unit data/raw data/processed docs`.
- [X] T002 Initialize a Python project with requirements.txt. Execute: `pip freeze > code/requirements.txt` containing: pandas, scikit-learn, xgboost, pymatgen, requests, pyyaml, matplotlib, seaborn, statsmodels, pytest.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `src/utils/constants.py` with atomic weights, unit conversion factors (Kelvin, GPa), and VIF threshold constants (established benchmarks)
- [ ] T005 [P] Implement `src/utils/logging.py` with standardized loggers for ingestion, modeling, and visualization
- [ ] T006 Implement `src/utils/data_provenance.py` with function `generate_provenance_header(source: str, timestamp: str, version: str) -> dict`. Verify the function returns a dictionary containing exactly these keys: `source`, `timestamp`, `version`. Create `tests/unit/test_provenance.py` to verify these keys are present.
- [ ] T007 [P] Setup `tests/unit/test_constants.py` and `tests/unit/test_logging.py` to verify utility modules
- [ ] T008 Configure environment variable handling for API keys (Materials Project) in `src/utils/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Consolidate MgB₂ data from Materials Project API and SuperCon dataset, standardize units, and filter for valid entries.

**Independent Test**: T015 (Integration Test) orchestrates T012, T013, and T014 sequentially to produce `data/processed/mgb2_clean.csv` with non-null Tc/impurities, standardized atomic %, and provenance header.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (verify columns: Tc, impurities_atomic_pct, temp_K, pressure_GPa)
- [~] T010 [P] [US1] Unit test for unit conversion logic in `tests/unit/test_preprocessing.py` (weight% to atomic% edge cases)
- [X] T011 [P] [US1] Unit test for data filtering in `tests/unit/test_ingestion.py` (verify rows with missing Tc/impurities are dropped)

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/ingestion/download_materials_project.py` to fetch Mg-B entries via API, handling rate limits and empty responses (exit code 1 if empty)
- [ ] T013 [P] [US1] Implement `src/ingestion/download_supercon.py` to fetch `taqwa92/cm.mgb2` from HuggingFace; **FAIL with exit code 1 if >50% of entries lack impurity columns**. Verification: Add unit test in `tests/unit/test_ingestion.py` using a synthetic dataset with a significant proportion of nulls to confirm exit code 1.
- [ ] T014 [US1] Implement `src/ingestion/preprocess.py` to merge datasets, convert units (weight% -> atomic%), handle synthesis ranges (midpoint imputation), and attach provenance metadata. **Verification**: Ensure provenance metadata is attached to CACHED files (bypassing T012/T013) as per FR-001.
- [ ] T015 [US1] Implement `tests/integration/test_pipeline.py` to run full ingestion flow (T012->T013->T014) and verify `mgb2_clean.csv` integrity (count > 0, no nulls in target columns)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Selection (Priority: P2)

**Goal**: Train Linear Regression, Ridge Regression, Random Forest, and XGBoost models with strict CPU limits, select best via cross-validated R².

**Independent Test**: Running `src/modeling/train.py` produces `data/processed/best_model.pkl` and a metrics report listing R²/MAE for all models.

### Tests for User Story 2

- [ ] T016 [P] [US2] Unit test for stratified splitting logic in `tests/unit/test_modeling.py` (verify rare impurity binning)
- [ ] T017 [P] [US2] Unit test for hyperparameter grid limits in `tests/unit/test_modeling.py` (verify ≤10 combinations enforced)

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `src/modeling/train.py` to load `mgb2_clean.csv`, perform stratified split (impurity type), and train **Linear Regression**, **Ridge Regression** (Plan-authorized for collinearity), Random Forest, and XGBoost.
- [ ] T019 [US2] Implement hyperparameter tuning logic in `src/modeling/train.py` with a hard cap on the number of grid combinations. **Implementation**: Use `signal` module or `threading.Timer` to enforce a configurable runtime watchdog as per Constitution Principle VII. Abort with clear error if exceeded.
- [ ] T020 [US2] Implement model selection logic in `src/modeling/train.py` to choose best model by cross-validated R² and save `best_model.pkl`
- [ ] T021 [US2] Generate `data/processed/model_metrics.json` containing R², MAE, and hyperparameters for all trained variants
- [ ] T022 [US2] Implement `tests/integration/test_modeling.py` to verify `best_model.pkl` loads and predicts on held-out data

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Interpretation (Priority: P3)

**Goal**: Validate impurity impact significance (p < 0.05) and generate Partial Dependence Plots for top 3 impurities.

**Independent Test**: Running `src/modeling/significance_test.py` and `src/visualization/plot_pdp.py` produces a report with p-values and 3 PDF/PNG plots.

### Tests for User Story 3

- [ ] T023 [P] [US3] Unit test for ANOVA calculation in `tests/unit/test_significance.py` (verify p-value output for linear model)
- [ ] T024 [P] [US3] Unit test for Permutation Test in `tests/unit/test_significance.py` (verify null distribution generation for tree models)

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/modeling/significance_test.py` to calculate VIF for all predictors. If VIF ≥ 5.0, group/remove collinear predictors and output a `reduced_feature_set.csv`. **Depends on**: T020 (Model Training)
- [ ] T026a [US3] Re-run significance testing logic on the `reduced_feature_set.csv` (output of T026) to ensure valid p-values on the non-collinear set. **Depends on**: T026
- [ ] T025 [US3] Implement `src/modeling/significance_test.py` to perform ANOVA (Linear) or **Feature Permutation Importance** (shuffling feature column X, re-predicting, comparing to baseline) for tree models. **Logic**: This implements the Plan's correction to FR-004. Filter features by p < 0.05. **Depends on**: T026a
- [ ] T025a [US3] **Documentation**: Create `docs/fr004_deviation_report.md` explicitly documenting why the Spec's "Target Permutation Test" (shuffling Y) was not implemented (methodologically invalid) and confirming the use of "Feature Permutation" as per Plan.
- [ ] T027 [US3] Implement `src/visualization/plot_pdp.py` to generate Partial Dependence Plots for the top significant impurities (ΔTc per atomic %)
- [ ] T028 [US3] Implement `src/modeling/significance_test.py` to generate a "Rule of Thumb" table. **Output**: `data/processed/rule_of_thumb.csv` with schema: `Impurity`, `ΔTc_per_atomic_pct`, `Method` (Coefficient or SHAP).
- [ ] T029 [US3] Implement `tests/integration/test_validation.py` to verify p-values are reported and plots are generated for significant impurities only

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates: Update `README.md` with Installation, Usage, Data Sources, and API Key Setup sections; update `docs/` with final architecture diagrams
- [ ] T031 Code cleanup: Refactor `src/ingestion/preprocess.py` to reduce cyclomatic complexity < 10 and remove code duplication
- [ ] T032 Performance optimization: Profile pipeline runtime; optimize data loading in `preprocess.py` and grid search in `train.py` to ensure total runtime < 30 mins on GitHub Actions
- [ ] T033 [P] Run `quickstart.md` validation
- [ ] T034 Update `data-model.md` with final entity definitions derived from implementation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained model from US2

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
# Launch all tests for User Story 1 together:
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Unit test for unit conversion logic in tests/unit/test_preprocessing.py"
Task: "Unit test for data filtering in tests/unit/test_ingestion.py"

# Launch implementation tasks (sequential dependency):
Task: "Implement download_materials_project.py" -> "Implement download_supercon.py" -> "Implement preprocess.py"
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