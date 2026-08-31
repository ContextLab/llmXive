# Tasks: Predicting the Impact of Additive Manufacturing Parameters on the Porosity of 316L Stainless Steel

**Input**: Design documents from `/specs/001-predicting-impact-of-additive-manufa/`
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

- [X] T001a [P] Create `code/`, `tests/`, `data/`, `results/`, `models/` directories at repository root. **Verification**: Run `ls -R` to confirm directory structure exists.
- [X] T001b [P] Create `projects/PROJ-363-predicting-the-impact-of-additive-manufa/` subdirectory structure if required by plan. **Verification**: Run `ls -R projects/PROJ-363-predicting-the-impact-of-additive-manufa/` to confirm structure.
- [X] T002 Initialize Python project with `requirements.txt` (pandas, scikit-learn, shap, matplotlib, seaborn, pyyaml, jsonschema).
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools. **Verification**: Run `ruff --version` and `black --version` to confirm installation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `contracts/dataset.schema.yaml` defining required columns (power, speed, hatch, thickness, porosity) and types.
- [X] T005 [P] Implement `code/utils.py` with helper functions for logging, seed setting, and state hash updating.
- [X] T007 Create `state/` directory and initial `state.yaml` for artifact versioning.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download a public LPBF 316L dataset, parse CSVs, handle missing values, normalize features, and engineer Volumetric Energy Density.

**Independent Test**: Verify the existence of `data/processed/cleaned_316L.csv` containing normalized columns, zero nulls, and the derived `energy_density` column.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download_data.py` to fetch the verified 316L LPBF dataset from a canonical source (Zenodo/OpenML). **Constraint**: Do NOT implement synthetic fallbacks; let network failures raise hard exceptions. **Logic**: If the dataset size exceeds ~10MB or the source supports it, use `datasets.load_dataset(..., streaming=True)` to process in chunks; otherwise, download the file directly. Update `state.yaml` with the SHA-256 checksum of the raw file.
- [X] T012b [US1] Implement `code/download_data.py` to perform a "Material Mismatch" check immediately after fetching. **Logic**: 1) Query the Zenodo/OpenML API record metadata for "316L" or "Stainless Steel" in the title/description. 2) If API metadata is unavailable, parse the first 5 rows of the CSV for a "material" column or header containing "316L". 3) If NEITHER check confirms 316L, raise a specific "Material Mismatch" error and halt execution. Update `state.yaml` with the checksum of the raw file.
- [X] T013 [US1] (Merged into T012) Checksum logic and state update.
- [X] T017 [US1] Implement `code/preprocess.py` contract validation step: Load `contracts/dataset.schema.yaml` (Depends on T004) and validate raw data structure BEFORE any transformation. Exit with clear error if validation fails.
- [X] T014 [US1] Implement `code/preprocess.py` to load raw data, map column synonyms (e.g., "P" -> "laser_power"), and impute missing numerical values using the **median** of the respective column. **Logic for Ev**: If raw parameters (power, speed, hatch, thickness) are present, **calculate** `VolumetricEnergyDensity` ($E_v = P / (v \cdot h \cdot t)$) for every record where parameters > 0. If raw parameters are missing but an `energy_density` column exists, **use** the provided column. **Only** if NEITHER raw parameters nor an energy density column exist, raise a clear error and halt. Do NOT fall back to synthetic data.
- [X] T015 [US1] Implement `code/preprocess.py` to detect "Degenerate Dataset" (zero porosity variance). If detected, raise a specific "Degenerate Dataset" error and halt execution.
- [X] T016a [US1] Implement `code/preprocess.py` to normalize input features (power, speed, hatch, thickness) to [0, 1] range.
- [X] T016b [US1] Implement `code/preprocess.py` to create distinct feature subsets: `X_raw` (only raw parameters) and `X_derived` (only Ev) to enforce FR-010 (no multicollinearity). Save both subsets to `data/processed/`.
- [X] T018 [US1] Save final processed dataset to `data/processed/cleaned_316L.csv` and update `state.yaml` with the new hash.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Contract tests ensure data integrity before modeling. These tasks depend on implementation tasks and CANNOT run in parallel with them.

- [ ] T009 [US1] Contract test: Validate `data/processed/cleaned_316L.csv` against `contracts/dataset.schema.yaml` in `tests/contract/test_dataset_schema.py` (Depends on T018)
- [X] T010 [US1] Unit test: **Write** logic to verify median imputation with synthetic missing data in `tests/unit/test_preprocessing.py` (Can be written in parallel with T014 logic, executed after)
- [X] T011b [US1] Unit test: **Write** logic to verify normalization scaling to [0, 1] range in `tests/unit/test_preprocessing.py` (Can be written in parallel with T016a logic, executed after)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean data ready).

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train Gradient Boosting and MLP regression models using k-fold cross-validation on the preprocessed data, and evaluate performance.

**Independent Test**: Verify generation of two model files (`.pkl`) in `models/artifacts/`, a JSON report in `results/reports/` with RMSE/R² for 5 folds.

### Implementation for User Story 2 (Raw Parameters)

- [X] T021 [US2] Implement `code/train_models.py` to load `data/processed/cleaned_316L.csv` (Depends on T018) and the `X_raw` subset (Depends on T016b), split into features (X) and target (y).
- [X] T022 [US2] Implement `code/train_models.py` to train a Gradient Boosting Regressor on `X_raw` using 5-fold CV, ensuring no GPU usage.
- [X] T023 [US2] Implement `code/train_models.py` to train a Multi-Layer Perceptron (MLP) Regressor on `X_raw` using 5-fold CV, ensuring CPU-only execution and fixed seed.
- [X] T024 [US2] Implement `code/train_models.py` to compute RMSE and R² for each of the 5 folds and the aggregate mean performance for `X_raw` models.
- [X] T025 [US2] Save trained Gradient Boosting and MLP models (trained on `X_raw`) to `models/artifacts/` (`.pkl` format).
- [X] T026 [US2] Save performance metrics (RMSE, R² per fold, mean) for `X_raw` to `results/reports/model_metrics_raw.json`.
- [X] T027 [US2] Update `state.yaml` with hashes of model artifacts and metrics report for `X_raw`.
- [X] T027b [US2] Verify SC-001: Explicitly instantiate `sklearn.dummy.DummyRegressor(strategy='mean')`, run 5-fold CV on `X_raw`, compute mean R², and compare it against the best model's mean R². Log the result (PASS/FAIL) in `results/reports/model_metrics_raw.json` under the key `dummy_baseline_check`.

### Implementation for User Story 2 (Derived Feature Subset)

- [X] T021b [US2] Implement `code/train_models.py` to load `data/processed/cleaned_316L.csv` and the `X_derived` subset, split into features (X) and target (y).
- [X] T022b [US2] Implement `code/train_models.py` to train a Gradient Boosting Regressor on `X_derived` using 5-fold CV.
- [X] T023b [US2] Implement `code/train_models.py` to train a Multi-Layer Perceptron (MLP) Regressor on `X_derived` using 5-fold CV.
- [X] T024b [US2] Implement `code/train_models.py` to compute RMSE and R² for each of the 5 folds and the aggregate mean performance for `X_derived` models.
- [X] T025b [US2] Save trained Gradient Boosting and MLP models (trained on `X_derived`) to `models/artifacts/` (`.pkl` format).
- [X] T026b [US2] Save performance metrics (RMSE, R² per fold, mean) for `X_derived` to `results/reports/model_metrics_derived.json`.
- [X] T027c [US2] Update `state.yaml` with hashes of model artifacts and metrics report for `X_derived`.
- [X] T027d [US2] Verify SC-001 for Derived Subset: Explicitly instantiate `sklearn.dummy.DummyRegressor(strategy='mean')`, run 5-fold CV on `X_derived`, compute mean R², and compare it against the best model's mean R². Log the result (PASS/FAIL) in `results/reports/model_metrics_derived.json` under the key `dummy_baseline_check`.

### Model Selection Logic

- [X] T028 [US2] **Model Selection**: Implement logic to parse `results/reports/model_metrics_raw.json` and `results/reports/model_metrics_derived.json`. Compare the mean R² scores of the best models from each subset. Select the model (raw or derived) with the **highest** mean R². Write the selection decision (model type, path, R² score) to `state/selected_model.yaml`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test: Verify 5-fold CV splits are reproducible with fixed seed in `tests/unit/test_training.py`
- [X] T020 [P] [US2] Unit test: Verify CPU-only execution constraint (no CUDA device assignment) in `tests/unit/test_training.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (models trained and evaluated on both subsets).

---

## Phase 5: User Story 3 - Explainability and Statistical Analysis (Priority: P3)

**Goal**: Generate SHAP plots and perform statistical significance testing (Permutation Importance + Bootstrap CIs) to interpret model drivers.

**Independent Test**: Verify generation of a SHAP summary plot in `results/plots/` and a statistical report table in `results/reports/` with p-values < 0.05.

### Implementation for User Story 3 (Selected Best Model)

- [X] T030 [US3] Implement `code/analyze_explainability.py` to **load** the model selected in T028 (read from `state/selected_model.yaml`). **Logic**: If `state/selected_model.yaml` indicates `X_raw`, load `models/artifacts/best_raw_model.pkl` and `data/processed/X_raw.csv`. If `X_derived`, load `models/artifacts/best_derived_model.pkl` and `data/processed/X_derived.csv`.
- [X] T031 [US3] Implement `code/analyze_explainability.py` to **calculate SHAP values** and generate a summary plot saved to `results/plots/shap_summary_{selected_subset}.png`.
- [X] T033c [US3] **Statistical Significance Integration**: Implement `code/analyze_explainability.py` to:
    1.  **Permutation Importance**: Run `sklearn.inspection.permutation_importance` with `n_repeats=1000` (or 100 if time-constrained, but target 1000) on the selected model.
    2.  **Bootstrap Resampling**: Run 1000 bootstrap iterations on the SHAP values (or permutation scores) to generate a distribution.
    3.  **P-Value Calculation**: Calculate p-values using the formula: `p = 2 * min(count(|perm| >= |obs|), count(|perm| <= |obs|)) / N`.
    4.  **Significance Filter**: Filter features where `p < 0.05`.
    5.  **Output**: Save the final statistical report (feature importance, p-values, 95% CIs) to `results/reports/significance_report_{selected_subset}.json`.

### Comparison and Reporting

- [X] T034 [US3] Ensure `code/analyze_explainability.py` explicitly logs the sample size (N) used for Permutation Importance and Bootstrap resampling, and states the confidence level (95%) in the output report header.
- [X] T034b [US3] Implement `code/analyze_explainability.py` to **compare** the feature importance and SHAP values from `X_raw` (if available) and `X_derived` (if available) to validate physical intuition, generating a comparison report in `results/reports/feature_comparison.json`.
- [X] T036 [US3] Update `state.yaml` with hashes of plots and statistical reports.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test: Verify Permutation Importance runs with 1,000 permutations and returns a valid score distribution.
- [X] T029 [P] [US3] Unit test: Verify Bootstrap Confidence Interval calculation logic.

**Checkpoint**: All user stories should now be independently functional (explainability and insights generated).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` (README, usage instructions). **Note**: This task is currently pending re-planning to address specific deliverable requirements.
- [X] T038 Code cleanup and refactoring of `code/utils.py` and error handling
- [X] T040 [P] Verify all artifacts in `state.yaml` match the latest hashes

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
- **User Story 2 (P2)**: Depends on US1 completion (requires `cleaned_316L.csv` and T016b feature subsets)
- **User Story 3 (P3)**: Depends on US2 completion (requires trained models AND T028 model selection)

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
- **Revision Note**: Phase 7 removed. Robustness logic (streaming, material check) was invalid or misplaced. Valid robustness (error handling) is now integrated into Phase 3 tasks (T012, T014). Added tasks to train and analyze both `X_raw` and `X_derived` subsets to satisfy US-3 comparison requirement. Explicitly added T012b for Material Mismatch check to satisfy plan.md Verified Accuracy Gate. Added T027d for dummy baseline on derived subset. Added T028 for model selection logic. Consolidated statistical tasks into T033c. Marked Phase 1 tasks as [X] with verification steps.