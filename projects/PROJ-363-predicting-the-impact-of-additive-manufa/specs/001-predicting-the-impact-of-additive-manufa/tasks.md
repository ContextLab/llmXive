# Tasks: Predicting the Impact of Additive Manufacturing Parameters on the Porosity of 316L Stainless Steel

**Input**: Design documents from `/specs/001-predicting-impact-of-additive-manufacturing-parameters-on-porosity/`
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

- [ ] T001a [P] Create `code/`, `tests/`, `data/`, `results/`, `models/` directories at repository root
- [ ] T001b [P] Create `projects/PROJ-363-predicting-the-impact-of-additive-manufa/` subdirectory structure if required by plan
- [ ] T002 Initialize Python project with `requirements.txt` (pandas, scikit-learn, shap, matplotlib, seaborn, pyyaml, jsonschema)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `contracts/dataset.schema.yaml` defining required columns (power, speed, hatch, thickness, porosity) and types
- [ ] T005 [P] Implement `code/utils.py` with helper functions for logging, seed setting, and state hash updating
- [~] T006 [P] Setup `code/` directory structure with `__init__.py` and placeholder files for data, models, and results
- [ ] T007 Create `state/` directory and initial `state.yaml` for artifact versioning
- [~] T008 Configure environment configuration management (`.env` example and loading logic in `utils.py`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download a public LPBF 316L dataset, parse CSVs, handle missing values, normalize features, and engineer Volumetric Energy Density.

**Independent Test**: Verify the existence of `data/processed/cleaned_316L.csv` containing normalized columns, zero nulls, and the derived `energy_density` column.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download_data.py` to fetch the verified 316L LPBF dataset from Zenodo (ID: - placeholder for actual ID, use specific URL like `), verify material type is 316L, and save to `data/raw/`.
- [~] T013 [US1] Implement `code/download_data.py` checksum logic (SHA-256) and update `state.yaml` after download.
- [X] T014 [US1] Implement `code/preprocess.py` to load raw data, map column synonyms (e.g., "P" -> "laser_power"), and implement fallback logic: FIRST check if a 'VolumetricEnergyDensity' (or similar) column exists; if present, use it. If not, check raw parameters; filter rows where scan_speed <= 0, hatch_spacing <= 0, or layer_thickness <= 0. Assign sentinel value -1.0 for missing raw parameters if Ev is used.
- [X] T015 [US1] Implement `code/preprocess.py` to detect "Degenerate Dataset" (zero porosity variance). If detected, raise a specific "Degenerate Dataset" error and halt execution (do not filter).
- [X] T016 [US1] Implement `code/preprocess.py` to normalize input features (power, speed, hatch, thickness) to [0, 1] and calculate `VolumetricEnergyDensity` for valid rows where raw parameters are available.
- [~] T017 [US1] Implement `code/preprocess.py` contract validation step: Load `contracts/dataset.schema.yaml` and exit if validation fails.
- [ ] T018 [US1] Save final processed dataset to `data/processed/cleaned_316L.csv` and update `state.yaml` with the new hash.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Contract tests ensure data integrity before modeling. These tasks depend on implementation tasks and CANNOT run in parallel with them.

- [~] T009 [US1] Contract test: Validate `data/processed/cleaned_316L.csv` against `contracts/dataset.schema.yaml` in `tests/contract/test_dataset_schema.py` (Depends on T018)
- [X] T010 [US1] Unit test: Verify median imputation logic with synthetic missing data in `tests/unit/test_preprocessing.py` (Depends on T014)
- [X] T011 [US1] Unit test: Verify normalization scaling to [0, 1] range in `tests/unit/test_preprocessing.py` (Depends on T016) <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
  in "<unicode string>", line 2, column 17:
            contents: |
                    ^) -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean data ready).

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train Gradient Boosting and MLP regression models using 5-fold cross-validation on the preprocessed data, and evaluate performance.

**Independent Test**: Verify generation of two model files (`.pkl`) in `models/artifacts/`, a JSON report in `results/reports/` with RMSE/R² for 5 folds.

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/train_models.py` to load `data/processed/cleaned_316L.csv` (Depends on T018), split into features (X) and target (y).
- [ ] T022 [US2] Implement `code/train_models.py` to train a Gradient Boosting Regressor using 5-fold CV, ensuring no GPU usage.
- [ ] T023 [US2] Implement `code/train_models.py` to train a Multi-Layer Perceptron (MLP) Regressor using 5-fold CV, ensuring CPU-only execution and fixed seed.
- [ ] T024 [US2] Implement `code/train_models.py` to compute RMSE and R² for each of the 5 folds and the aggregate mean performance.
- [ ] T025 [US2] Save trained Gradient Boosting and MLP models to `models/artifacts/` (`.pkl` format).
- [ ] T026 [US2] Save performance metrics (RMSE, R² per fold, mean) to `results/reports/model_metrics.json`.
- [ ] T027 [US2] Update `state.yaml` with hashes of model artifacts and metrics report.
- [ ] T027b [US2] Verify SC-001: Explicitly compute a dummy regressor baseline (e.g., `DummyRegressor` with strategy='mean') on the same 5-fold CV splits, compare the best model's mean R² against the dummy baseline, and log the result (PASS/FAIL) in `results/reports/model_metrics.json`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test: Verify 5-fold CV splits are reproducible with fixed seed in `tests/unit/test_training.py`
- [ ] T020 [P] [US2] Unit test: Verify CPU-only execution constraint (no CUDA device assignment) in `tests/unit/test_training.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (models trained and evaluated).

---

## Phase 5: User Story 3 - Explainability and Statistical Analysis (Priority: P3)

**Goal**: Generate SHAP plots and perform statistical significance testing (Permutation Importance + Bootstrap CIs) to interpret model drivers.

**Independent Test**: Verify generation of a SHAP summary plot in `results/plots/` and a statistical report table in `results/reports/` with p-values < 0.05.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/analyze_explainability.py` to load the best performing model (from `models/artifacts/`) (Depends on T025) and the processed dataset.
- [ ] T031 [US3] Implement `code/analyze_explainability.py` to calculate SHAP values and generate a summary plot saved to `results/plots/shap_summary.png`.
- [ ] T032 [US3] Implement `code/analyze_explainability.py` to perform Permutation Importance with exactly 1,000 permutations to determine feature significance.
- [ ] T033b [US3] Implement `code/analyze_explainability.py` to perform bootstrap resampling with exactly 1,000 iterations to calculate 95% Bootstrap Confidence Intervals for SHAP values.
- [ ] T033 [US3] Implement `code/analyze_explainability.py` to calculate p-values from the bootstrap distribution and identify statistically significant parameters (p < 0.05).
- [ ] T034 [US3] Ensure `code/analyze_explainability.py` does NOT use both raw parameters and Volumetric Energy Density simultaneously as inputs (avoid multicollinearity).
- [ ] T035 [US3] Save statistical significance report (feature importance, p-values, CIs) to `results/reports/significance_report.json`.
- [ ] T036 [US3] Update `state.yaml` with hashes of plots and statistical reports.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test: Verify Permutation Importance runs with 1,000 permutations and returns a valid score distribution.
- [ ] T029 [P] [US3] Unit test: Verify Bootstrap Confidence Interval calculation logic.

**Checkpoint**: All user stories should now be independently functional (explainability and insights generated).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` (README, usage instructions)
- [ ] T038 Code cleanup and refactoring of `code/utils.py` and error handling
- [ ] T039 [P] Run `quickstart.md` validation to ensure full pipeline reproducibility
- [ ] T040 [P] Verify all artifacts in `state.yaml` match the latest hashes

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
- **User Story 2 (P2)**: Depends on US1 completion (requires `cleaned_316L.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (requires trained models)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementing
- Models before services (not applicable here, but logic applies to script order)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- Once US1 completes, US2 and US3 cannot start in parallel (US3 depends on US2)

---

## Parallel Example: User Story 1

```bash
# Launch implementation tasks sequentially:
Task: "Implement download_data.py" -> "Implement preprocess.py" -> "Run validation"

# Launch tests after implementation:
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Unit test for median imputation in tests/unit/test_preprocessing.py"
Task: "Unit test for normalization in tests/unit/test_preprocessing.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (clean data exists)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Models trained)
4. Add User Story 3 → Test independently → Deploy/Demo (Insights generated)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: Foundational/Contracts (if not done)
3. Once US1 completes:
 - Developer A: User Story 2 (Training)
 - Developer B: User Story 3 (Explainability - can prepare logic in parallel but needs model)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Tasks with explicit "Depends on" must be executed in that order; [P] tag is removed from dependent test tasks.