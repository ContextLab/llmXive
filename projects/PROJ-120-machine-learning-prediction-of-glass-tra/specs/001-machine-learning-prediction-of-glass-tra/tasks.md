# Tasks: Machine Learning Prediction of Glass Transition Temperature from Composition

**Input**: Design documents from `/specs/001-machine-learning-prediction-of-glass-tra/`
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

- [ ] T001a Create directory: `projects/PROJ-120-machine-learning-prediction-of-glass-tra/`
- [ ] T001b Create directory: `data/`
- [ ] T001c Create directory: `code/`
- [ ] T001d Create directory: `tests/`
- [ ] T001e Create directory: `artifacts/`
- [ ] T001f Create directory: `state/`
- [~] T002a Initialize Python virtualenv in `projects/PROJ-120-machine-learning-prediction-of-glass-tra/.venv`
- [X] T002b Generate `code/requirements.txt` pinning: pymatgen, matminer, scikit-learn, shap, pandas, numpy, requests, pytest
- [~] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [~] T004 Setup data directories (`data/raw`, `data/processed`, `artifacts`, `state`)
- [X] T005 [P] Implement `code/utils.py` with shared helpers (logging, checksum verification)
- [X] T006 [P] Create base data models: `code/data_models.py` (GlassSample, ModelResult, Dataset)
- [~] T007 Setup environment configuration management (`.env` handling for Zenodo DOI)
- [~] T008 Configure error handling infrastructure (custom exceptions for data fetch failures)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Compositional Featurization (Priority: P1) 🎯 MVP

**Goal**: Ingest raw oxide glass data from the NIST Materials Data Repository (via Zenodo), parse formulas, and generate a feature matrix containing network-former ratios, modifier content, and average electronegativity.

**Independent Test**: The pipeline executes on the NIST dataset, producing a `.csv` with composition-only features (e.g., `avg_electronegativity`, `network_modifier_ratio`) and no missing $T_g$ values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. These must be written before implementation tasks.**

- [X] T010 [US1] Unit test for formula parsing in `tests/test_featurize.py` (verify `pymatgen` Composition handling)
- [X] T011 [US1] Unit test for compositional descriptor calculation in `tests/test_featurize.py` (verify network former/modifier ratio logic)

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/download_data.py` to fetch raw CSV from NIST Materials Data Repository (via Zenodo) (FAIL LOUDLY on failure, no synthetic fallback)
- [X] T013 [P] [US1] Implement `code/featurize.py` to parse chemical formulas using `pymatgen.Composition`
- [X] T014 [US1] Implement **composition-only** descriptor calculation in `code/featurize.py`:
 - Calculate **Atomic Fractions** for Network Formers (Si, B, P) and Modifiers (Na, K, Ca)
 - Calculate **Network Former/Modifier Ratio** (Sum of Si+B+P atomic fractions vs Sum of Na+K+Ca atomic fractions)
 - Calculate **Average Electronegativity** (weighted by atomic fraction)
 - Calculate **Average Atomic Mass** and **Total Valence Electron Count**
 - **Exclude** any structural descriptors (e.g., Coordination Number, NBO, Bond Valence) as per Constitution Principle VI
- [X] T015 [US1] Implement `code/featurize.py` elemental property extraction using `matminer.ElementProperty` (Electronegativity, Atomic Mass, Valence)
- [ ] T016 [US1] Add domain validity check: Verify mean SiO2 fraction is within expected oxide glass range; halt with error if mismatched
- [ ] T017 [US1] Add logging for data fetch, parsing errors (invalid formulas), and exclusion counts
- [ ] T018 [US1] Save featurized dataset to `data/processed/glass_features.csv` with columns: `formula`, `Tg`, `network_former_ratio`, `avg_electronegativity`, `avg_atomic_mass`, `valence_electron_count` (NO structural columns)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train tree-based models (RF, GB) and compare against a physics-based linear mixing rule baseline that respects stoichiometric constraints, evaluating if composition alone predicts $T_g$ beyond simple additive rules.

**Independent Test**: The training script runs within CPU constraints, outputs `artifacts/model_performance.json` with R², MAE, RMSE, and a paired t-test p-value comparing ML vs. Baseline using MAE values from 5 folds.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for Linear Mixing Rule calculation in `tests/test_baseline.py` (verify stoichiometric conversion logic)
- [ ] T020 [P] [US2] Unit test for statistical significance test (paired t-test) in `tests/test_evaluate.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/baseline.py` to compute Linear Mixing Rule:
 - Map elemental fractions to oxide mole fractions (Si→SiO2, Na→Na2O) using a **strict stoichiometric conversion algorithm**
 - Handle excess oxygen by prioritizing modifiers
 - Use dataset mean $T_g$ for pure oxides with undefined values
- [ ] T022 [US2] Implement `code/train.py` to train `RandomForestRegressor` and `GradientBoostingRegressor`
 - Grid search: `n_estimators` ∈ {100, 300}, `max_depth` ∈ {10, 20}
 - Select best model based on R² on validation fold
- [ ] T023 [US2] Implement 5-fold Cross-Validation (or Bootstrap if N < 50) in `code/train.py`
 - **Output Requirement**: Must generate and save a list of **scalar MAE values** (one per fold) for both the ML model and the Linear Mixing Baseline.
 - **Artifact**: `artifacts/cv_fold_mae.json` containing lists of 5 scalars for ML and Baseline.
- [ ] T024 [US2] Implement `code/evaluate.py` to calculate R², MAE, RMSE on held-out test set
- [ ] T025 [US2] Implement paired t-test in `code/evaluate.py` comparing **scalar MAE values obtained from the 5 cross-validation folds** (one scalar per fold) of ML vs. Baseline.
 - **Input**: The list of 5 MAE scalars from T023 for ML and the list of 5 MAE scalars for Baseline.
 - **Output**: p-value from paired t-test.
 - **Constraint**: Do NOT use sample-level residuals. Use only fold-level MAE scalars.
- [ ] T026 [US2] Handle small dataset edge case: If N < 50, skip t-test and use Bootstrap resampling to generate confidence intervals for R² and MAE
- [ ] T027 [US2] Save results to `artifacts/model_performance.json` (R², MAE, RMSE, p-value, model type, hyperparameters)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

**Goal**: Extract feature importances using SHAP and perform compositional-aware permutation importance to validate rankings while respecting sum-to-one constraints, ensuring model robustness.

**Independent Test**: The analysis script outputs a ranked feature list (top 5 drivers) and a sensitivity report showing MAE variance across hyperparameter grids.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for SHAP value extraction in `tests/test_interpret.py`
- [ ] T029 [P] [US3] Unit test for sensitivity analysis logic in `tests/test_interpret.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `code/interpret.py` to extract feature importances using `shap.TreeExplainer` (avoids sum-to-one constraint violation of standard permutation)
- [ ] T031 [US3] Implement **compositional-aware permutation importance** validation:
 - Shuffle top 3 features using a method that respects the **sum-to-one constraint** (e.g., Dirichlet sampling or constrained shuffling)
 - Measure R² drop (must be < 0.5 of original)
 - **Calculate Spearman rank correlation** between SHAP rankings and permutation rankings.
 - **Verify**: Correlation must be ≥ 0.8 (per SC-004).
 - **Output**: Save the correlation coefficient and pass/fail status to `artifacts/interpretability_report.json`.
- [ ] T032 [US3] Implement sensitivity analysis in `code/interpret.py`:
 - Sweep `n_estimators` ∈ {100, 300} and `max_depth` ∈ {10, 20}
 - Calculate MAE variance.
 - **Verify**: Standard deviation of MAE must be ≤ 5% of mean MAE (per SC-003).
 - **Output**: Record the mean MAE, std dev, and pass/fail status in `artifacts/interpretability_report.json`.
- [ ] T033 [US3] Generate interpretability report: Top 5 drivers (e.g., "Network Former Ratio", "Avg Electronegativity", "Valence Electron Count") with importance scores
- [ ] T034 [US3] Save interpretability results to `artifacts/interpretability_report.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure scientific rigor

- [ ] T035 [P] Update `research.md` to reflect the **composition-only hypothesis**: testing if compositional descriptors alone predict $T_g$ beyond linear mixing, without assuming structural drivers
- [ ] T036a [P] Remove unused imports from all files in `code/`
- [ ] T036b [P] Optimize memory usage in `code/featurize.py` (ensure streaming if dataset > 7GB)
- [ ] T036c [P] Add type hints to all functions in `code/`
- [ ] T037 Performance optimization: Ensure data loading streams if dataset > 7GB (though current dataset is expected to fit in RAM)
- [ ] T038 [P] Add comprehensive docstrings to all functions in `code/`
- [ ] T039 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T040 Verify all tasks in `tasks.md` are executable in order and produce expected artifacts

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (featurized data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (trained model)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- **Sequential Order**: Write Tests -> Verify Fail -> Implement -> Verify Pass.
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (with each other, but NOT with implementation)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for formula parsing in tests/test_featurize.py"
Task: "Unit test for compositional descriptor calculation in tests/test_featurize.py"

# Launch all implementation for User Story 1 together:
Task: "Implement code/download_data.py to fetch raw CSV from NIST (via Zenodo)"
Task: "Implement code/featurize.py to parse chemical formulas"
Task: "Implement compositional descriptor calculation (Atomic Fractions, Ratios, Electronegativity)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data + Compositional Featurization)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify compositional descriptors are calculated correctly)
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
 - Developer A: User Story 1 (Data + Compositional Features)
 - Developer B: User Story 2 (Model Training + Baseline)
 - Developer C: User Story 3 (Interpretability + Sensitivity)
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
- **Revision Note**: Removed Phase 7 (Topological Proxies) to strictly adhere to Constitution Principle VI (Composition-Only) and FR-002. Updated T025 to explicitly require scalar MAE per fold (no residuals). Updated T031 and T032 to enforce SC-004 (Spearman correlation) and SC-003 (std dev) pass/fail logic. Split coarse setup/cleanup tasks (T001, T002, T036) for executability. Clarified test vs implementation ordering.