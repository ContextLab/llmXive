# Tasks: Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys

**Input**: Design documents from `/specs/001-predict-solder-hardness/`
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
 - Be implemented independently
 - Be tested independently
 - Be delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure per implementation plan: `projects/PROJ-328-predicting-the-impact-of-composition-on-/data/`, `code/`, `tests/`, and `models/`
- [ ] T002 Create `requirements.txt` at `projects/PROJ-328-predicting-the-impact-of-composition-on-/code/` with dependencies (PIN EXACT VERSIONS): `pandas`, `scikit-learn`, `xgboost`, `shap`, `numpy`, `matplotlib`, `pyyaml`, `requests`, `compositional`, `pdfplumber`, `pytest`, `flake8`, `black`
- [ ] T003 Configure linting (flake8/black) and formatting tools (must run after T001)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/seed.py` to pin random seeds for reproducibility (numpy, random, xgboost)
- [ ] T005 [P] Implement data ingestion scaffolding in `code/ingestion/` with placeholder for literature aggregator
- [ ] T006 [P] Setup `code/features/` directory structure for descriptor engineering
- [~] T007 Create base data models/entities (`SolderComposition`, `CompositionalDescriptor`) in `code/models/`
- [~] T008 Configure error handling and logging infrastructure in `code/utils/`
- [~] T009 Setup environment configuration management for paths and thresholds in `code/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Aggregate and validate solder hardness dataset (Priority: P1) 🎯 MVP

**Goal**: Aggregate ≥100 unique solder alloy compositions with Vickers hardness from open sources into a unified dataset with validation.

**Independent Test**: Execute ingestion pipeline on GitHub Actions free-tier runner and verify output dataset contains ≥100 unique compositions with non-null hardness values and complete elemental breakdowns. If 50 ≤ N < 100, verify warning is emitted.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [~] T010 [P] [US1] Contract test for data validation schema in `tests/contract/test_data_schema.py`
- [~] T011 [P] [US1] Integration test for ingestion pipeline in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [~] T012 [US1] Implement `code/ingestion/aggregator.py` to fetch data from the 'Verified Literature Corpus' (specific PDF URLs: [list from research.md] and database endpoints: Materials Project, NIST, OpenAlloy) using `pdfplumber` and `requests` <!-- FAILED: unspecified -->
- [~] T013 [US1] Implement data cleaning and filtering logic in `code/ingestion/cleaner.py` to:
 - Exclude alloys with >5 elements
 - Standardize hardness to HV units
 - Filter for room-temperature measurements only
 - Validate elemental composition sums to a threshold read from `code/config.py` (default 0.95, marked as provisional per spec.md FR-002 deferred status)
 - Implement random sampling logic with fixed seed (from T004) if dataset exceeds RAM limits (per FR-011)
- [~] T014 [US1] Implement validation logic in `code/ingestion/validator.py` to check for non-null hardness and complete composition, emitting power limitation warning if 50 ≤ N < 100
- [~] T015 [US1] Save raw immutable data to `data/raw/solder_hardness_raw.csv` with checksums in `data/checksums.txt`
- [ ] T016 [US1] Save validated dataset to `data/processed/solder_hardness_validated.csv`
- [ ] T017 [US1] Add logging for ingestion operations and data source citations in `code/ingestion/`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and compare composition-to-hardness regression models (Priority: P2)

**Goal**: Train XGBoost and linear regression models with cross-validation, bootstrap comparison, SHAP analysis, and VIF diagnostics.

**Independent Test**: Run model training on validated dataset and verify cross-validation metrics (R², RMSE) are computed, VIF scores are reported, and feature importance rankings are generated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [ ] T019 [P] [US2] Integration test for model training pipeline in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement CLR transform in `code/features/transformer.py` using `compositional` library to handle closure problem; output both the transformed vector and the weight coefficients for downstream use
- [ ] T021 [US2] Implement descriptor computation in `code/features/descriptor_engine.py` to calculate weighted mean atomic mass, electronegativity variance, atomic radius variance, weighted average melting point, and valence electron concentration by: 1) Applying CLR to raw composition vector, 2) Using the resulting CLR coefficients to weight the original raw elemental property tables (NOT computing properties on log-ratios)
- [ ] T022 [US2] Implement VIF calculation in `code/features/collinearity.py` to flag predictors with VIF ≥ 5
- [ ] T023 [US2] Implement XGBoost training with grid search (≤10 combinations) in `code/models/xgboost_trainer.py`
- [ ] T024 [US2] Implement Linear Regression baseline training in `code/models/linear_trainer.py`
- [ ] T025 [US2] Implement k-fold cross-validation for both models in `code/evaluation/cv.py`
- [ ] T026 [US2] Implement bootstrap resampling for confidence intervals on held-out test set in `code/evaluation/bootstrap.py`
- [ ] T027 [US2] Implement paired t-test comparison on CV folds in `code/evaluation/model_comparison.py`
- [ ] T028 [US2] Implement SHAP value calculation and top-3 feature ranking in `code/evaluation/shap_analysis.py`
- [ ] T029 [US2] Implement sensitivity analysis in `code/evaluation/sensitivity.py` sweeping R² thresholds over the specific set {0.3, 0.5, 0.6, 0.7} and saving the fraction of bootstrap samples exceeding each threshold to `data/processed/sensitivity_analysis.yaml` as per SC-005
- [ ] T030 [US2] Save model artifacts, metrics, and diagnostics to `models/` and `data/processed/`
- [ ] T031 [US2] Add associational framing warnings in ALL model outputs, visualizations, and the final report per FR-007

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate interpretable visualizations and partial dependence plots (Priority: P3)

**Goal**: Generate scatter plot of predicted vs. measured hardness with error bars and partial dependence plots for top 3 features.

**Independent Test**: Execute visualization pipeline and verify output files (scatter plot, 3 partial dependence plots) are generated with correct axis labels and units.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Contract test for visualization output schema in `tests/contract/test_viz_output.py`
- [ ] T033 [P] [US3] Integration test for visualization pipeline in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [ ] T034 [US3] Implement scatter plot generation in `code/visualization/scatter.py` with 95% CI error bars
- [ ] T035 [US3] Implement partial dependence plot generation in `code/visualization/pdp.py` for top 3 SHAP-ranked features
- [ ] T036 [US3] Implement sensitivity analysis plot in `code/visualization/sensitivity_plot.py`
- [ ] T037 [US3] Save all plots to `data/outputs/` with correct labels and units
- [ ] T038 [US3] Add axis labels, titles, and legends to all visualizations

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `README.md` and `docs/`
- [ ] T040 Code cleanup and refactoring
- [ ] T041 Performance optimization to ensure <6h runtime on free-tier
- [ ] T042 [P] Additional unit tests in `tests/unit/`
- [ ] T043 Run quickstart.md validation
- [ ] T044 Verify all tasks respect CPU-only constraints (no CUDA, no GPU, no 8-bit quantization)
- [ ] T045 Verify dataset size handling (sampling logic implemented in T013)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (except T003 which depends on T001)
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data validation schema in tests/contract/test_data_schema.py"
Task: "Integration test for ingestion pipeline in tests/integration/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement data cleaning and filtering logic in code/ingestion/cleaner.py"
Task: "Implement validation logic in code/ingestion/validator.py"
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

- [P] tasks = different files, no dependencies (except T003 which depends on T001)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All data must be real (no fabrication); all models must run on CPU-only; all datasets must be sampled if needed to fit available system memory