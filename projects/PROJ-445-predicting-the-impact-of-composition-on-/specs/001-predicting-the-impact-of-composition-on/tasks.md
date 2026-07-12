# Tasks: Predicting the Impact of Composition on the Glass Transition Temperature of Chalcogenide Glasses

**Input**: Design documents from `/specs/001-glass-transition-prediction/`
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

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python 3.11 project with `pandas`, `scikit-learn`, `shap`, `mendeleev`, `requests`, `numpy`, `pytest`, `statsmodels` dependencies in `requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `data/`, `artifacts/`, `state/` directory structure
- [X] T005 [P] Implement `state/manifest.json` initialization logic to track artifact hashes
- [X] T006 [P] Create `src/utils/constants.py` with periodic property helpers (coordination numbers, electronegativity, atomic radii) using `mendeleev`
- [X] T007a [P] Create `contracts/chalcogenide_sample.schema.yaml` per plan.md specification
- [X] T007b [P] Create `contracts/model_performance.schema.yaml` per plan.md specification
- [X] T007c [P] Create `contracts/shap_importance.schema.yaml` per plan.md specification
- [X] T007d [P] Create `contracts/shap_report.schema.yaml` per plan.md specification
- [X] T008 Configure error handling and logging infrastructure in `src/utils/logger.py` <!-- SKIPPED: non-mapping output -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Load and preprocess chalcogenide composition data with feature engineering (Priority: P1) 🎯 MVP

**Goal**: Download the chalcogenide dataset, compute compositional descriptors (mean coordination number, electronegativity variance, atomic radius variance), and prepare a stratified train/test split.

**Independent Test**: Execute the data loading script and verify that (a) the dataset loads without errors, (b) all required features are computed for each sample with complete source data, and (c) the train/test split maintains ≥80% training proportion with stratification by chemical family.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for data download retry logic in `tests/unit/test_download.py`
- [~] T010 [P] [US1] Unit test for feature engineering (MCN, electronegativity variance) in `tests/unit/test_feature_engineering.py` <!-- SKIPPED: non-mapping output -->
- [~] T011 [P] [US1] Integration test for stratified split logic in `tests/integration/test_split.py`

### Implementation for User Story 1

- [~] T012 [US1] Implement `src/data/download.py` to fetch dataset from supplementary repository URL, validate columns (composition, Tg), handle HTTP errors with 3 retries, and **explicitly generate the marker string `DATA_MISSING: Required column [column_name] not found`** (writing to log and `state/manifest.json`) if any required column is missing (per SC-005), then compute checksums for `state/manifest.json`
- [~] T013 [US1] Implement `src/data/preprocess.py` to compute mean coordination number, electronegativity variance, and atomic radius variance using `mendeleev`, excluding samples with incomplete formulas. **If predictors are present, explicitly write the success marker `Dataset variable availability is confirmed...` to `state/variable_fit.log`. If predictors are missing, write `DATA_MISSING: Predictor [name] not found`.** (per SC-008).
- [~] T014 [US1] Implement `src/data/split.py` to perform stratified split (≥80% train) by chemical family. **If any chemical family in the split has <10 samples, the system MUST switch to full Leave-One-Family-Out (LOFO) cross-validation for the entire dataset, replacing the stratified split entirely**, and log this decision (per Constitution Principle VII).
- [~] T015 [US1] Implement power analysis in `src/data/preprocess.py` to estimate Minimum Detectable Effect Size (MDES). **If power < 0.80, write a JSON artifact to `state/power_analysis.json` with schema `{"power": <float>, "power_limitation_message": "Power Limitation: Insufficient power to detect small effects"}`** (per SC context).
- [~] T016 [US1] Add validation to ensure all derived features are recorded in `data/processed/` with content hashes in `state/manifest.json`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and evaluate gradient boosting model against linear baseline (Priority: P2)

**Goal**: Train a Gradient Boosting Regressor using scikit-learn on CPU with 5-fold cross-validation, tune hyperparameters, and compare performance (RMSE, R²) against a linear regression baseline.

**Independent Test**: Execute the training script and verify that (a) the gradient boosting model trains without GPU/CUDA dependencies, (b) 5-fold CV completes within the 6-hour CI time limit, and (c) performance metrics (RMSE, R²) are computed for both models on the held-out test set.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T017 [P] [US2] Unit test for model training (CPU-only check) in `tests/unit/test_train.py`
- [~] T018 [P] [US2] Integration test for cross-validation timing and metrics in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [~] T022 [US2] Implement `src/utils/metrics.py` to compute Variance Inflation Factors (VIF) for compositional descriptors. **If VIF ≥ 5, trigger residualization logic and document the specific mitigation strategy in `performance_metrics.json` using the key `collinearity_mitigation` with value `residualization`** (per SC-007).
- [~] T023 [US2] Implement `src/models/train.py` to generate residualized features (orthogonalized heterogeneity descriptors) **conditionally** if T022 detects VIF ≥ 5, and save to `data/residualized/` with checksums in `state/manifest.json`.
- [~] T019 [US2] Implement `src/models/train.py` to train Linear Regression baseline and Gradient Boosting Regressor using `scikit-learn` (default float64, no quantization) with 5-fold CV. **This task must run AFTER T022/T023 to ensure it uses residualized features if collinearity is detected.**
- [~] T020 [US2] Implement hyperparameter tuning for Gradient Boosting within `src/models/train.py`, ensuring search space is constrained to meet 6-hour CI limit

#### Sub-phase: Analysis & Mitigation (Conditional on Data)
*These tasks depend on the output of T019 and must run before final evaluation if collinearity is detected.*

- [~] T021 [US2] Implement `src/models/evaluate.py` to compute RMSE and R² for both models on the held-out test set and log results
- [~] T024 [US2] Implement a utility function in `src/utils/metrics.py` to generate the explicit "ASSOCIATIONAL, NOT CAUSAL" disclaimer text, **writing it to `artifacts/causal_disclaimer.txt`** (per FR-008), to be consumed by T031.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate SHAP analysis and feature importance report (Priority: P3)

**Goal**: Apply SHAP analysis to quantify the contribution of each descriptor to Tg predictions, compute 95% bootstrapped confidence intervals, and produce a report identifying which features drive model predictions.

**Independent Test**: Execute the SHAP analysis script and verify that (a) SHAP values are computed for all features, (b) a feature importance ranking is produced, and (c) the report identifies the relative contribution of chemical heterogeneity descriptors versus mean coordination number.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T025 [P] [US3] Unit test for SHAP value computation (CPU-only) in `tests/unit/test_explain.py`
- [~] T026 [P] [US3] Integration test for bootstrapped confidence interval calculation in `tests/integration/test_metrics.py`

### Implementation for User Story 3

- [~] T027 [US3] Implement `src/models/explain.py` to sample dataset to ≤5000 samples if necessary (per SC-006) and use `shap.TreeExplainer` for Gradient Boosting model
- [~] T028 [US3] Compute mean absolute SHAP values for all features and rank them in `src/models/explain.py`
- [~] T029 [US3] Implement 95% bootstrapped confidence intervals for the difference in mean absolute SHAP values between chemical heterogeneity and mean coordination number in `src/utils/metrics.py`. **Apply family-wise error rate control (e.g., Bonferroni or Holm-Bonferroni) for multiple-comparison correction when testing >1 hypothesis (per SC-009)**. **Write `ci_lower`, `ci_upper`, and `is_significant` fields to `performance_metrics.json`** (per SC-006).
- [~] T025 [US3] **Train N-1 distinct Gradient Boosting models**, each excluding one chemical family from the training set, and save these artifacts to `data/models/lofo_models/` with checksums. **This task is a prerequisite for T030.**
- [~] T030 [US3] Implement Cross-Family Transferability Test in `src/models/explain.py` (train on N-1 families, test on held-out) and compare feature importances. **Explicitly depend on the completion of T025 (N-1 model training artifacts) before computing SHAP for comparison.**
- [~] T031 [US3] Generate `shap_report.md` in `artifacts/` including: feature importance ranking, CI results, transferability metrics. **Must read `state/power_analysis.json`, extract the `power_limitation_message` field, and include it in the report under the heading "Power Analysis". Must also read `artifacts/causal_disclaimer.txt` and insert it into a dedicated section titled "Causal Disclaimer" (per FR-008).**
- [~] T032 [US3] Generate `performance_metrics.json` in `artifacts/` with RMSE, R², MDES, VIF, CI lower/upper bounds, `is_significant`, and transferability flags (per SC-006, SC-007)
- [~] T033 [US3] Record all SHAP subset hashes and report artifacts in `state/manifest.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T034 [P] Documentation updates in `docs/` including run instructions and data dictionary
- [~] T035 Code cleanup and refactoring to ensure CPU-only compliance
- [~] T036 Performance optimization: verify 5-fold CV completes within 6 hours on free-tier runner
- [~] T037 [P] Additional unit tests for edge cases (missing columns, small strata) in `tests/unit/`
- [~] T038 Run `quickstart.md` validation to ensure full pipeline reproducibility
- [~] T039 Final verification of `state/manifest.json` integrity and artifact checksums

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
- Data download/preprocessing before split
- Split before model training
- Model training before SHAP analysis
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
Task: "Unit test for data download retry logic in tests/unit/test_download.py"
Task: "Unit test for feature engineering in tests/unit/test_feature_engineering.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/download.py"
Task: "Implement src/data/preprocess.py"
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
- **Critical Constraint**: All tasks MUST run on free-tier CI (2 CPU, ~7 GB RAM, no GPU) within 6 hours. No -bit/4-bit quantization or CUDA dependencies allowed.
- **Data Integrity**: All analysis must use REAL data from the downloaded source. No fabricated or synthetic data generation is permitted.