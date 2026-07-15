# Tasks: Predicting Material Stability using Machine Learning and DFT Calculations

**Input**: Design documents from `/specs/001-material-stability/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-116-predicting-material-stability-using-mach/`
- [X] T002 Initialize Python 3.11 project with dependencies in `projects/PROJ-116-predicting-material-stability-using-mach/code/requirements.txt` (pymatgen, scikit-learn, pandas, numpy, matplotlib, seaborn, requests, datasets, shap)
- [ ] T003 [P] Configure linting and formatting tools in `projects/PROJ-116-predicting-material-stability-using-mach/code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup logging infrastructure in `projects/PROJ-116-predicting-material-stability-using-mach/code/utils/logging.py` with file and console handlers
- [ ] T005 [P] Create base data models for `MaterialEntry` and `FeatureVector` in `projects/PROJ-116-predicting-material-stability-using-mach/code/__init__.py` or `data_models.py`
- [ ] T006 Setup environment configuration management for data paths and random seeds in `projects/PROJ-116-predicting-material-stability-using-mach/code/config.py`
- [X] T007 Implement data validation utilities to check for missing bond lengths and degenerate Voronoi cells in `projects/PROJ-116-predicting-material-stability-using-mach/code/utils/validation.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Model Training and Evaluation (Priority: P1) 🎯 MVP

**Goal**: Train a Gradient Boosting Regressor using only bulk compositional descriptors (Magpie features) on the filtered OQMD dataset to establish a performance baseline.

**Independent Test**: The system can be fully tested by training the baseline model on a majority training split, evaluating it on a held-out test split, and outputting a CSV containing predicted formation energies and calculated MAE/RMSE metrics without any local coordination features.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for Magpie feature extraction logic in `projects/PROJ-116-predicting-material-stability-using-mach/tests/unit/test_features.py`. **Dependencies**: Explicitly requires completion of T005 (data models) and T007 (validation utilities) to ensure testable interfaces exist.
- [X] T011 [P] [US1] Integration test for baseline training pipeline end-to-end in `projects/PROJ-116-predicting-material-stability-using-mach/tests/integration/test_baseline.py`. **Dependencies**: Explicitly requires completion of T005 (data models) and T007 (validation utilities) to ensure testable interfaces exist.

### Implementation for User Story 1

- [~] T012 [US1] Implement `download_data.py` to fetch OQMD data, filter for Li-rich rock-salt structures, and save to `projects/PROJ-116-predicting-material-stability-using-mach/data/raw/` (FR-001). Explicitly log a warning if the sample count is less than a sufficient threshold and proceed with available data.
- [ ] T013 [US1] Implement `feature_engineering.py` to compute bulk Magpie features only. Handle missing values by imputing with dataset median. **Explicitly log the count of skipped entries or imputed values to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/logs/imputation_log.txt`**. Output to `projects/PROJ-116-predicting-material-stability-using-mach/data/processed/baseline_features.parquet`.
- [ ] T014 [US1] Implement `train_baseline.py` to train a Gradient Boosting Regressor on Magpie features with hyperparameter tuning on a validation split. Save model to `projects/PROJ-116-predicting-material-stability-using-mach/data/models/baseline_model.pkl` and save the tuning results (best params, scores) to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/baseline_tuning_results.json`. **Verify that best_params and validation_scores are recorded in the JSON.**
- [ ] T015 [US1] Implement evaluation logic in `evaluate.py` to generate predictions on the test set and calculate MAE/RMSE. Output results to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/baseline_results.csv`.
- [ ] T016 [US1] Add validation to ensure `baseline_results.csv` contains predicted formation energies and metrics even if error > 0.1 eV/atom.
- [ ] T017 [US1] Add logging for dataset size, feature count, and training metrics in `projects/PROJ-116-predicting-material-stability-using-mach/outputs/logs/`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Local Coordination Feature Integration and Comparative Analysis (Priority: P2)

**Goal**: Augment the dataset with local coordination environment features (Voronoi statistics, bond-length distributions) and train a second model to determine if these features significantly reduce prediction error compared to the baseline.

**Independent Test**: The system can be fully tested by executing the feature engineering step to generate local descriptors, training the augmented model, and producing a comparative report showing the delta in MAE and R² between the baseline and the augmented model.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for Voronoi tessellation and bond-length histogram calculation in `projects/PROJ-116-predicting-material-stability-using-mach/tests/unit/test_voronoi_features.py`. **Dependencies**: Explicitly requires completion of T005 (data models) and T012 (raw data availability).
- [ ] T019 [P] [US2] Integration test for augmented model training and comparison in `projects/PROJ-116-predicting-material-stability-using-mach/tests/integration/test_augmented.py`. **Dependencies**: Explicitly requires completion of T005 (data models) and T012 (raw data availability).

### Implementation for User Story 2

- [ ] T020 [US2] Extend `feature_engineering.py` to compute local coordination features (Voronoi stats: coordination number, face area, solid angle; bond-length histograms) **using pymatgen on the raw crystal structures from data/raw/ (produced by T012)**. Append to the feature matrix.
- [ ] T021 [US2] Implement logic to handle degenerate Voronoi cells or missing bond lengths by skipping the feature for that entry and logging the count.
- [ ] T022 [US2] Save the augmented feature set to `projects/PROJ-116-predicting-material-stability-using-mach/data/processed/augmented_features.parquet`.
- [ ] T023 [US2] Implement `train_augmented.py` to train a second Gradient Boosting Regressor on the combined feature set **with hyperparameter tuning performed on the validation split**. Save model to `projects/PROJ-116-predicting-material-stability-using-mach/data/models/augmented_model.pkl` and save tuning results to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/augmented_tuning_results.json`. **Verify that the tuning results are recorded in the JSON.**
- [ ] T024 [US2] Implement comparative analysis in `evaluate.py` to calculate MAE and R² for the augmented model and the delta relative to the baseline. Output results to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/comparison_metrics.json` (must include MAE_delta and R2_delta).
- [ ] T025 [US2] Generate a feature importance plot (SHAP or Permutation) highlighting the top local coordination features. Save to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/figures/feature_importance.png`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Metastable Phase Classification and Sensitivity Analysis (Priority: P3)

**Goal**: Classify materials as stable or metastable (defined as < 0.05 eV/atom above the convex hull) and perform a sensitivity analysis on this threshold to ensure the findings are robust to small variations in the cutoff.

**Independent Test**: The system can be fully tested by running the classification module on the test set predictions, calculating the AUC-ROC, and executing a sensitivity sweep over a range of threshold values to report the variation in recall/precision.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T035 [P] [US3] Unit test for convex hull distance calculation using `pymatgen` in `projects/PROJ-116-predicting-material-stability-using-mach/tests/unit/test_hull_distance.py`
- [ ] T036 [P] [US3] Integration test for sensitivity analysis sweep in `projects/PROJ-116-predicting-material-stability-using-mach/tests/integration/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T037 [US3] Implement convex hull distance calculation using `pymatgen` `PhaseDiagram` for all predictions and ground truth values. **Handle cases where pymatgen fails due to missing elemental references by excluding the entry from classification metrics but RETAINING it in the regression analysis, logging the reason. Verify that the filtered dataset for regression contains N entries (where N = total - excluded_count).**
- [ ] T037b [US3] **Save the calculated hull distances for all entries to `projects/PROJ-116-predicting-material-stability-using-mach/data/processed/hull_distances.parquet`.** This artifact is required for downstream classification and sensitivity tasks.
- [ ] T038 [US3] Implement classification logic to label materials as "stable" (distance ≤ 0.00) or "metastable" (0.00 < distance ≤ threshold). **Depends on T037b (hull_distances.parquet).**
- [ ] T039 [US3] Implement ROC curve generation and AUC-ROC calculation in `evaluate.py`. Save the plot to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/figures/roc_curve.png` and the metric to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/metrics/roc_auc.json`.
- [ ] T040 [US3] Implement sensitivity analysis script to sweep thresholds around the 0.05 eV/atom region. Calculate Recall, Precision, F1, and **calculated variance in false-positive/false-negative rates** for each. **Output results to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/sensitivity_analysis.csv` containing columns: threshold, recall, precision, F1, variance_fp, variance_fn.** **Verify that sensitivity_analysis.csv exists and contains the required columns.** **Depends on T037b (hull_distances.parquet) and predictions from T015/T024.**
- [ ] T041a [US3] **Calculate variance metrics (Recall variance, Precision variance) from `sensitivity_analysis.csv` and save to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/metrics/variance_summary.json`.** **Depends on T040.**
- [ ] T041b [US3] Generate the final robustness report in `projects/PROJ-116-predicting-material-stability-using-mach/outputs/robustness_report.md` by analyzing `variance_summary.json`. Explicitly state if the model's ability to distinguish metastable phases is robust (variance < 5%) or sensitive to the threshold choice. **Depends on T041a.**
- [ ] T042 [US3] Add logging for dataset size, feature count, and training metrics in `projects/PROJ-116-predicting-material-stability-using-mach/outputs/logs/`.
- [ ] T043 [US3] Perform a Permutation Test for model validation to handle non-normal error distributions. Shuffle the target labels (formation energy) to generate a null distribution of performance metrics and compare against the actual model performance. **Requires trained models from T014 and T023.** Save the p-value and test statistics to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/metrics/permutation_test_results.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Run full pipeline benchmark to measure total runtime and memory footprint, ensuring ≤ 4 hours and ≤ 7 GB RAM. Output to `projects/PROJ-116-predicting-material-stability-using-mach/outputs/performance_metrics.json`.
- [ ] T045 Code cleanup and refactoring of feature engineering scripts to optimize for CPU-only execution.
- [ ] T046 [P] Additional unit tests for edge cases (e.g., empty dataset, missing bond lengths) in `projects/PROJ-116-predicting-material-stability-using-mach/tests/unit/`.
- [ ] T047 Validate `quickstart.md` instructions against the implemented pipeline.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data download (T012) and feature engineering base (T013)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on predictions from US1 and US2 (T015, T024) and hull distances (T037b)

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
Task: "Unit test for Magpie feature extraction logic in projects/PROJ-116-predicting-material-stability-using-mach/tests/unit/test_features.py"
Task: "Integration test for baseline training pipeline end-to-end in projects/PROJ-116-predicting-material-stability-using-mach/tests/integration/test_baseline.py"

# Launch all models for User Story 1 together:
Task: "Implement download_data.py to fetch OQMD data..."
Task: "Implement feature_engineering.py to compute bulk Magpie features..."
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