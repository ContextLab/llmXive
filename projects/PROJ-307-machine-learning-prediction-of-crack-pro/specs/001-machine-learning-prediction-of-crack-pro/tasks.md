# Tasks: Machine Learning Prediction of Crack Propagation Rates in Metals

**Input**: Design documents from `/specs/001-crack-propagation-ml/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001a [P] Create directory structure for `projects/001-crack-propagation-ml/` (code, data, tests, specs, contracts)
- [~] T001b [P] Create initial `__init__.py` files and empty placeholder files for `code/` modules

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Create project structure per implementation plan (`projects/001-crack-propagation-ml/`)
- [X] T003 Initialize Python 3.11 project with `pyproject.toml` and pinned `requirements.txt` (scikit-learn, xgboost, optuna, pandas, ruptures, matplotlib, seaborn, pyyaml, jsonschema)
- [X] T004 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T005 [P] Create `code/config.py` for hyperparameters, random seeds, and path configuration
- [ ] T006 [P] Create `contracts/dataset.schema.yaml` defining required columns ($da/dN$, $\Delta K$, composition, heat treatment)
- [ ] T007 [P] Create `contracts/output.schema.yaml` defining expected result formats (metrics, plots)
- [X] T008 [P] Create `code/utils/__init__.py` and `code/utils/stats.py` (file structure for stats module)
- [~] T009 [P] Create skeleton `code/data/loader.py` with schema validation logic (consumes `contracts/dataset.schema.yaml` from T006)
- [~] T010 [P] Setup environment configuration management and logging infrastructure in `code/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Validation and Dataset Preparation (Priority: P1) 🎯 MVP

**Goal**: Ingest public FCG datasets, clean data, impute missing heat-treatment values, and establish a physics-based baseline (Paris Law) using linear regression.

**Independent Test**: The pipeline runs on a subset, outputs a linear regression model with $R^2$, and generates a partial dependence plot showing the log-log linear relationship.

### Implementation for User Story 1

- [X] T013 [US1] Implement data fetching logic in `code/data/loader.py` to fetch real data from **NASA Fracture Control Database** (CSV: `) and **NIST Materials Data Repository** (CSV: `). Save to `data/raw/` with checksums. **DO NOT** use `numenta/NAB` or generic repos. <!-- FAILED: unspecified -->
- [X] T014 [US1] Implement `code/data/preprocessor.py` to filter valid $da/dN$/$\Delta K$, impute missing heat-treatment with "Unknown/Not Specified", and encode features
- [X] T015 [US1] Implement `code/models/baseline.py` for stratified linear regression using only $\log(\Delta K)$ to predict $\log(da/dN)$
- [X] T016 [US1] Implement `code/main.py` step to train baseline and calculate $R^2$ and p-value against a **null model defined as an intercept-only (horizontal line) model** using a **Permutation Test** to confirm the **log-log linear relationship of the Paris Law** (slope significance).
- [X] T017 [US1] Implement `code/analysis/viz.py` to generate Partial Dependence Plot (PDP) for $\Delta K$ vs $da/dN$ verifying Paris Law linearity
- [~] T018 [US1] Add validation logic to halt if dataset lacks required columns after cleaning
- [X] T010 [US1] Unit test for `code/data/loader.py` schema validation in `tests/unit/test_loader.py` (Write test immediately after T013 code)
- [X] T011 [US1] Unit test for `code/data/preprocessor.py` imputation logic in `tests/unit/test_preprocessor.py` (Write test immediately after T014 code)
- [X] T012 [US1] Integration test for baseline model training and $R^2$ calculation in `tests/integration/test_baseline.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Augmented Model Training and Variance Explanation (Priority: P2)

**Goal**: Train tree-based ensemble models (RF, XGBoost) with composition and heat-treatment features, and quantify variance explained via Permutation Tests.

**Independent Test**: The system trains the augmented model, performs k-fold CV, and outputs a $\Delta R^2$ metric with $p \le 0.05$ from a Permutation Test.

### Implementation for User Story 2

- [X] T007a [P] [US2] Implement the core Permutation Test function in `code/utils/stats.py` (parameters: n_permutations, seed, metric). **Null Hypothesis**: Target values are randomly permuted. **Test Statistic**: Difference in $R^2$ between models. **P-value**: Proportion of permuted statistics >= observed statistic.
- [X] T021 [US2] Implement `code/models/augmented.py` to support Random Forest and XGBoost with composition (wt%) and heat-treatment descriptors
- [X] T019 [US2] Unit test for `code/models/augmented.py` fallback logic (missing features) in `tests/unit/test_augmented.py`
- [ ] T022 [US2] Implement `code/models/trainer.py` using Optuna for hyperparameter tuning ($n\_estimators$, $max\_depth$, $learning\_rate$) with k-fold stratified CV
- [ ] T023 [US2] Implement `code/main.py` step to perform Permutation Test (using logic from T007a) comparing Baseline vs. Augmented model error reduction. **Note**: Implementation follows Plan.md decision to use ONLY Permutation Tests (F-test rejected).
- [ ] T020 [US2] Integration test for Permutation Test significance in `tests/integration/test_permutation.py`
- [ ] T024 [US2] Implement `code/main.py` step to train augmented models, run CV, and calculate $\Delta R^2$
- [ ] T025 [US2] Implement feature importance aggregation and top-3 feature extraction logic in `code/analysis/`
- [ ] T026 [US2] Add fallback logic in `code/models/augmented.py` to handle missing composition or heat-treatment columns gracefully

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regime Identification and Sensitivity Analysis (Priority: P3)

**Goal**: Identify $\Delta K$ regions where microstructural effects dominate using continuous interaction analysis and verify stability via sensitivity analysis.

**Independent Test**: The system generates a regime map showing $\Delta R^2$ across regions and a sensitivity report confirming stability under parameter variation.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/analysis/regimes.py` using **`ruptures` change-point detection** as the primary method to identify Low/Mid/High $\Delta K$ regions. **Fallback**: If `ruptures` fails, use `scikit-learn`'s `GaussianProcessRegressor` with RBF kernel (varying coefficient model) with bandwidth selected via cross-validation.
- [ ] T027 [US3] Unit test for `code/analysis/regimes.py` varying coefficient models in `tests/unit/test_regimes.py`
- [ ] T030 [US3] Implement local $R^2$ and feature importance calculation within identified regimes in `code/analysis/regimes.py`
- [ ] T031 [US3] Implement `code/analysis/sensitivity.py` to sweep model parameters and verify region stability (ranking unchanged)
- [ ] T028 [US3] Unit test for `code/analysis/sensitivity.py` stability check in `tests/unit/test_sensitivity.py`
- [ ] T032 [US3] Implement `code/analysis/viz.py` to generate regime maps and PDPs for top 3 non-$\Delta K$ features
- [ ] T033 [US3] Implement `code/main.py` step to orchestrate regime analysis and generate final sensitivity report
- [ ] T034 [US3] Implement logic to evaluate model on held-out distinct alloy families. **If** the primary dataset lacks distinct families, **execute graceful degradation**: log a warning that generalizability test is limited to available data and proceed with evaluation on the existing subset. **DO NOT** fetch secondary external data.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `README.md`: Update 'Installation' (dependencies), 'Data Sources' (NASA/NIST URLs), 'Usage' (example commands), and 'Results' (interpretation of PDPs).
- [ ] T036 Code cleanup and refactoring for memory efficiency (< 7 GB RAM)
- [ ] T037 Performance optimization to ensure full pipeline completes within 6 hours on 2-core CPU
- [ ] T038 [P] Additional unit tests for data validation edge cases in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation and CI pipeline verification
- [ ] T040 [P] Update `spec.md` to remove the "nested model F-test" option from FR-005, formally ratifying the Plan.md decision to use only Permutation Tests.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data cleaning pipeline
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model outputs

### Within Each User Story

- **TDD Discipline**: Tests are written *immediately after* the implementation block they validate (e.g., T013 then T010, T014 then T011).
- Data loading/preprocessing before modeling
- Modeling before analysis/viz
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
# Launch implementation and test for T013/T010 together (TDD flow):
Task: "Implement data fetching logic in code/data/loader.py..." (T013)
Task: "Unit test for code/data/loader.py schema validation..." (T010)

# Launch implementation and test for T014/T011 together:
Task: "Implement code/data/preprocessor.py to filter valid data..." (T014)
Task: "Unit test for code/data/preprocessor.py imputation logic..." (T011)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Implementation -> Tests)
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
- **TDD Workflow**: Write implementation code, then immediately write the corresponding test task to validate it. The list order reflects execution flow (Code -> Test), but development discipline requires Test-Driven thinking.
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All data fetching tasks MUST use real, reachable URLs or package-based fetchers (no fake/synthetic data generation).
- **CRITICAL**: All models MUST run on CPU-only CI (2 cores, 7GB RAM) within 6 hours. No GPU/8-bit dependencies.
- **CRITICAL**: Data sources MUST be NASA Fracture Control Database and NIST Materials Data Repository.
- **CRITICAL**: Generalizability tests MUST be performed even if primary data lacks diversity (graceful degradation if needed).
- **CRITICAL**: Regime analysis MUST prioritize `ruptures` as per Plan.md, with fallback to varying coefficient models.
- **CRITICAL**: All statistical tests (T016, T023) MUST use Permutation Tests as per Plan.md.