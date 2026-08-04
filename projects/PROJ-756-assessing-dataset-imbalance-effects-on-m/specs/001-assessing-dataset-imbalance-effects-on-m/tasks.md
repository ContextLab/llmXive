# Tasks: Assessing Dataset Imbalance Effects on Materials Property Predictions

**Input**: Design documents from `/specs/001-assess-dataset-imbalance-effects/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-756-assessing-dataset-imbalance-effects-on-m/`, `data/`, `code/`, `tests/`, `artifacts/`, `results/`, `state/`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, scikit-learn, shap, magpie, datasets, numpy, scipy, pyyaml, cvxpy)
- [X] T003 [P] Configure linting (ruff/black) and formatting tools in root `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/ingestion.py` with exponential backoff (5 retries, 60s timeout) for OQMD and AFLOW APIs, and merge data (FR-001, FR-007, FR-008) <!-- ATOMIZE: requested -->
- [X] T005 Implement `code/ingestion.py` fallback logic: if Materials Project API fails (403/timeout), log scope change and proceed with OQMD/AFLOW only
- [ ] T006 Implement data downloaders to save raw CSV/Parquet to `data/raw/` with checksum verification (Constitution III)
- [X] T007 Implement `code/descriptors.py` to compute all 14 Magpie compositional descriptors (L2-normalized) and save to `data/processed/` (FR-002)
- [X] T008 Implement `code/imbalance.py` to calculate Target Imbalance Score (Gini of target values) and skip properties with <100 samples (FR-002, FR-011)
- [X] T009 Implement `code/imbalance.py` to calculate Compositional Imbalance Score using the Gini coefficient of the compositional feature space (derived from K-Means clustering with k=50 and Euclidean distance) (FR-002)
- [X] T010 [P] Create unit tests for ingestion retry logic and API failure handling in `tests/unit/test_ingestion.py`
- [X] T011 [P] Create unit tests for Magpie descriptor computation in `tests/unit/test_descriptors.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Quantify Imbalance and Generate Baseline Predictions (Priority: P1) 🎯 MVP

**Goal**: Download datasets, compute descriptors, train baseline RF/GB models on skewed data, and generate baseline performance report.

**Independent Test**: Can be fully tested by running `code/ingestion.py`, `code/descriptors.py`, and `code/training.py` (baseline mode) to produce a CSV report with MAE, RMSE, R² for skewed data.

### Tests for User Story 1 (Contract & Integration) ⚠️

- [ ] T012 [P] [US1] Contract test for data schema validation in `tests/contract/test_dataset_schema.py` (validates `data/processed/` against `contracts/dataset.schema.yaml`)
- [X] T013 [P] [US1] Integration test for baseline pipeline in `tests/integration/test_baseline_pipeline.py` (runs ingestion -> descriptors -> baseline training -> report)

### Implementation for User Story 1

- [X] T014 [US1] Implement `code/training.py` to train Random Forest and Gradient Boosting regressors on skewed data (FR-004)
- [X] T015 [US1] Implement `code/training.py` to evaluate models on a stratified test set preserving original imbalance (FR-004)
- [ ] T016 [US1] Implement `code/evaluation.py` to generate baseline performance report (MAE, RMSE, R²) per property and save to `results/baseline_report.csv` (US-1) <!-- FAILED: unspecified -->
- [X] T017 [US1] Implement `code/main.py` orchestration to run Ingestion -> Descriptors -> Imbalance Calc -> Baseline Training -> Evaluation
- [ ] T018 [US1] Add logging for all API errors and data ingestion failures with configurable retry counts (FR-007)
- [ ] T019 [US1] Verify Task T012 and T013 pass after baseline implementation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Apply Resampling and Measure Performance Degradation (Priority: P2)

**Goal**: Apply stratified resampling (or fallback), retrain models, and statistically compare performance on the minority subset.

**Independent Test**: Can be fully tested by running the resampling pipeline, producing a comparison table and statistical test results (paired t-test/Wilcoxon) showing performance difference on the bottom [deferred] subset.

### Tests for User Story 2 (Contract & Integration) ⚠️

- [ ] T020 [P] [US2] Contract test for resampling logic in `tests/contract/test_resampling_schema.py` (validates CV constraints)
- [X] T021 [P] [US2] Integration test for statistical significance in `tests/integration/test_statistical_significance.py` (validates power analysis and p-value calculation)

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/resampling.py` with stratified undersampling/oversampling using a dynamically determined number of equal-frequency bins, iterating to ensure bin counts have a Coefficient of Variation (CV) ≤ 0.10 (FR-003)
- [X] T023 [US2] Implement `code/resampling.py` fallback logic: if >20% data loss or empty bins occur with dynamic binning, switch to cost-sensitive learning (class weights) or SMOTE for regression (FR-003)
- [X] T024 [US2] Implement `code/resampling.py` constraint: CV ≤ 0.10 for the *real* data distribution in the balanced set (FR-003)
- [X] T025 [US2] Implement `code/training.py` to retrain RF and GB models on the balanced dataset with identical hyperparameters (FR-004)
- [X] T026 [US2] Implement `code/evaluation.py` to isolate the bottom [deferred] subset of the target distribution (dynamically determined by T028) and calculate per-bin MAE (FR-010) <!-- FAILED: unspecified -->
- [X] T027 [US2] Implement `code/evaluation.py` to calculate performance degradation: MAE_skewed_minority - MAE_balanced_minority (FR-009, SC-001)
- [X] T028 [US2] Implement `code/evaluation.py` power analysis (FR-015) to determine minimum random seeds for Cohen's d = 0.5, power ≥ 0.8, α = 0.05, and output the determined seed count for use by T029
- [ ] T029 [US2] Implement `code/evaluation.py` paired statistical tests (t-test/Wilcoxon) across determined random seeds (FR-005)
- [ ] T030 [US2] Implement `code/evaluation.py` to calculate correlation between Compositional Imbalance Score (Gini-based from T009) and performance degradation (FR-012)
- [ ] T031 [US2] Implement `code/evaluation.py` to calculate correlation between Target Imbalance Score and performance degradation (FR-012)
- [ ] T032 [US2] Generate comparison report (skewed vs. balanced) with statistical significance results in `results/comparison_report.csv` (US-2)
- [ ] T033 [US2] Verify Task T020 and T021 pass after resampling implementation

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze Feature Importance Distortion via SHAP (Priority: P3)

**Goal**: Generate SHAP values, compare top-10 feature rankings, and validate against a synthetic ground-truth baseline.

**Independent Test**: Can be fully tested by running the SHAP analysis script on trained models and synthetic data, producing a ranked list and visualization of rank shifts.

### Tests for User Story 3 (Contract & Integration) ⚠️

- [ ] T034 [P] [US3] Contract test for SHAP output schema in `tests/contract/test_shap_schema.py` (validates rank shift metrics)
- [ ] T035 [P] [US3] Integration test for synthetic ground truth validation in `tests/integration/test_shap_validation.py`

### Implementation for User Story 3

- [ ] T036 [US3] Implement `code/shap_analysis.py` to generate a synthetic dataset with known feature weights (non-linear, physics-like constraints) for ground truth validation (FR-014)
- [ ] T037 [US3] Implement `code/shap_analysis.py` to compute SHAP values for both skewed and balanced models (FR-006)
- [ ] T038 [US3] Implement `code/shap_analysis.py` to rank top-10 features for both models and calculate mean rank shift (ties broken by average rank) (FR-006, SC-003)
- [ ] T039 [US3] Implement `code/shap_analysis.py` to validate SHAP ranks against the synthetic ground truth to distinguish bias correction from distortion (FR-014)
- [ ] T040 [US3] Implement `code/shap_analysis.py` to visualize features that changed rank position significantly (e.g., top 5 skewed vs. top 20 balanced)
- [ ] T041 [US3] Generate SHAP comparison report and visualizations in `results/shap_analysis/` (US-3)
- [ ] T042 [US3] Verify Task T034 and T035 pass after SHAP implementation

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Documentation updates in `docs/` (README, quickstart.md, data-model.md)
- [ ] T044 Code cleanup and refactoring in `code/`
- [ ] T045 Add memory profiling to `code/training.py` and `code/shap_analysis.py` and log peak usage to `results/memory_profile.csv` to verify memory footprint < 7 GB (Constraint-002)
- [ ] T046 [P] Additional unit tests for edge cases (e.g., <100 samples property, API rate limits) in `tests/unit/`
- [ ] T047 Run `quickstart.md` validation to ensure full pipeline executes within 6 hours (Constraint-001)
- [ ] T048 Final review of `state/projects/PROJ-756-...yaml` for versioning completeness

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires baseline models from US1 for comparison
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires trained models from US1 and US2 for SHAP analysis

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
Task: "Contract test for data schema validation in tests/contract/test_dataset_schema.py"
Task: "Integration test for baseline pipeline in tests/integration/test_baseline_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingestion.py with exponential backoff"
Task: "Implement code/descriptors.py to compute Magpie descriptors"
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
 - Developer A: User Story 1 (Ingestion, Descriptors, Baseline)
 - Developer B: User Story 2 (Resampling, Statistics)
 - Developer C: User Story 3 (SHAP, Synthetic Ground Truth)
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
- **Data Constraint**: All data loaders MUST fail loudly on fetch errors; NO synthetic fallbacks allowed.
- **Compute Constraint**: Pipeline must run on CPU-only runner; if GPU is required for a method, it must be explicitly scaled down or offloaded, not faked.