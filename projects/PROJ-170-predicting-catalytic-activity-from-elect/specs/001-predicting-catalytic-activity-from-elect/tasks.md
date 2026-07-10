# Tasks: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

**Input**: Design documents from `/specs/001-predicting-catalytic-activity/`
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

**Purpose**: Project initialization and basic structure. All file system paths must be created here before any logic tasks run.

- [ ] T001a [P] Create project directory structure: `data/raw/`, `data/processed/`, `code/`, `outputs/`, `tests/`, `state/`, `code/models/`
- [ ] T001b [P] Create `__init__.py` files in all Python packages (`code/`, `tests/`, `code/utils/`)
- [ ] T001c [P] Initialize Python 3.10 project with `requirements.txt` (pinned versions: pandas, numpy, scikit-learn, xgboost, shap, requests, pyyaml, rdkit, huggingface_hub)
- [ ] T002 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure logic that MUST be complete before ANY user story can be implemented. 
**Note**: This phase assumes directory structure from Phase 1 (T001a) is already present.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement content hashing mechanism for `state/` artifacts (Constitution Principle V) in `code/utils/hashing.py`
- [ ] T005 [P] Create base configuration loader for environment variables and paths in `code/config.py`
- [ ] T006 [P] Setup logging infrastructure to write logs to `outputs/run.log`
- [ ] T007 [P] Implement data validation helpers (checksum verification, schema checks) in `code/utils/validation.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download OC20 stratified sample, align descriptors, impute missing values, and produce `aligned_dataset.csv`. 
**Scope Note**: Per plan.md "Critical Scope Adjustment", this pipeline relies exclusively on the verified OC20 dataset. External datasets (Materials Project, 2025 CO2 study) are excluded due to verification failures.

**Independent Test**: The pipeline can be tested by verifying that the output CSV contains exactly the expected columns (composition, surface_facet, energy_change, d_band_center, adsorption_energy) with no NaN values in the target column after imputation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T008 [P] [US1] Contract test for data alignment logic in `tests/test_preprocess.py::test_alignment_columns`
- [ ] T009 [P] [US1] Integration test for full download-to-csv flow in `tests/test_preprocess.py::test_full_pipeline_sample`

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/download_data.py`: Download stratified sample of OC dataset from HuggingFace (repo: 'oc20/oc20-sample-v1', stratify by 'composition_family', output: 'data/raw/oc20_sample.h5')
- [ ] T011 [US1] Implement `code/download_data.py`: Verify checksums of downloaded OC20 file against known hashes
- [ ] T014 [US1] Implement `code/preprocess.py`: Align OC20 entries using exact string matching on `composition` and `surface_facet`. **Note**: `synthesis_condition` alignment is deferred as per plan pivot to single-source OC20 data (FR-002 adaptation).
- [ ] T015 [US1] Implement `code/preprocess.py`: Retrieve target variable `energy_change` from OC20 data (per plan pivot). Log any missing target values for exclusion.
- [ ] T016 [US1] Implement `code/preprocess.py`: Compute and log alignment success rate (matched entries / total sample) for SC-002
- [ ] T017 [US1] Implement `code/preprocess.py`: Impute missing descriptors using k-nearest-neighbors (k=5) based on **stoichiometry similarity** (parse composition string into normalized element count vector, calculate Euclidean distance, exclude target from distance) (FR-003)
- [ ] T018 [US1] Implement `code/preprocess.py`: Handle edge case where <5 neighbors exist (flag and exclude from training set)
- [ ] T019 [US1] Implement `code/preprocess.py`: Scale all numeric features to zero mean and unit variance
- [ ] T020 [US1] Generate `data/processed/aligned_dataset.csv` with final schema
- [ ] T021 [US1] Create `tests/test_preprocess.py` unit tests for KNN imputation logic and exclusion flags

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train XGBoost model, compare against linear baseline, and perform statistical significance testing

**Independent Test**: The model training can be tested by running the script and verifying that both the XGBoost and linear models produce predictions on the hold-out test set with calculated R² and MAE metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Contract test for metric calculation in `tests/test_train.py::test_metrics_output`
- [ ] T023 [P] [US2] Integration test for nested CV flow in `tests/test_train.py::test_nested_cv_execution`

### Implementation for User Story 2

- [ ] T024 [US2] Implement `code/train.py`: Load `aligned_dataset.csv` and split into train/test sets (stratified). **Depends on T020 completion.**
- [ ] T025 [P] [US2] Implement `code/train.py`: Train Linear Baseline using only `d_band_center` and `adsorption_energy`
- [ ] T026 [US2] Implement `code/train.py`: Train XGBoost with nested cross-validation (inner loop: grid search max_depth {,5,7}, lr {0.01,0.1}, n_est ≤200; outer loop: R² evaluation) and **Save best model to code/models/best_xgboost.json** (FR-004)
- [ ] T027 [US2] Implement `code/evaluate.py`: Compute absolute errors for both models on hold-out test set. **Depends on T025 and T026 completion.**
- [ ] T028a [US2] Implement `code/evaluate.py`: Perform Shapiro-Wilk test on the distribution of absolute errors for the **baseline model** and **XGBoost model**; **Log result (normal/not normal) to outputs/normality_check.json** (FR-005)
- [ ] T028b [US2] Implement `code/evaluate.py`: Perform paired t-test (if normal) or Wilcoxon signed-rank test (if not normal) on absolute errors comparing XGBoost vs Linear baseline. **Depends on T028a.**
- [ ] T029 [US2] Generate `outputs/metrics.json` containing R², MAE, Pearson R, and p-value for both models
- [ ] T030 [US2] Create `tests/test_train.py` unit tests for grid search parameter selection logic

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Interpretability Analysis (Priority: P3)

**Goal**: Perform SHAP analysis, rank top descriptors, verify SC-003, and generate final report

**Independent Test**: The interpretability step can be tested by running the SHAP calculation and verifying that the top 5 descriptors are listed in descending order of importance with a corresponding bar plot generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Contract test for SHAP value computation in `tests/test_evaluate.py::test_shap_values`
- [ ] T032 [P] [US3] Integration test for reduced model verification in `tests/test_evaluate.py::test_reduced_model_sc003`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/evaluate.py`: Compute SHAP values for the final XGBoost model using `shap.TreeExplainer`. **Depends on T026 (model saved).**
- [ ] T034 [US3] Implement `code/evaluate.py`: Rank descriptors by mean absolute SHAP impact (FR-006)
- [ ] T035 [US3] Implement `code/evaluate.py`: Generate `outputs/feature_importance.png` bar plot of top 5 descriptors
- [ ] T036 [US3] Implement `code/evaluate.py`: Train a reduced model using only the top 5 SHAP-ranked descriptors
- [ ] T037 [US3] Implement `code/evaluate.py`: Verify SC-003: Check if reduced model R² ≥ 0.50 * full model R². **Append verification status to outputs/metrics.json**
- [ ] T038 [US3] Implement `code/evaluate.py`: Validate SC-003 threshold (0.50 R²) against target variable context; if target is 'energy_change', recalculate expected redundancy or flag as legacy threshold in report.
- [ ] T039 [US3] Implement `code/report.py`: Compare top 5 descriptors against Nørskov et al., reference list (d-band, activation barrier, reaction energy) and **Generate comparison table in outputs/final_report.md with columns: descriptor, norskov_match (boolean), novelty_flag** (FR-007)
- [ ] T040 [US3] Implement `code/report.py`: Generate `outputs/final_report.md` containing Pearson R, MAE, p-value, top 5 list, SC-003 verification result, and Nørskov comparison table (FR-007)
- [ ] T041 [US3] Create `tests/test_evaluate.py` unit tests for SC-003 threshold logic

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Run full pipeline end-to-end and verify completion within 6-hour CI limit (SC-004)
- [ ] T043a [P] Code cleanup: Remove debug prints from `code/preprocess.py` and `code/train.py`
- [ ] T043b [P] Code cleanup: Optimize memory usage in `code/train.py` by streaming data where possible
- [ ] T043c [P] Code cleanup: Format all code with `black` and `ruff`
- [ ] T044 [P] Update `README.md` with usage instructions and data sources
- [ ] T045 [P] Add additional unit tests for edge cases (missing neighbors, non-normal error distributions)
- [ ] T046 [P] Run quickstart.md validation to ensure reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T001a) - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs `aligned_dataset.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (needs trained XGBoost model)

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
Task: "Contract test for data alignment logic in tests/test_preprocess.py::test_alignment_columns"
Task: "Integration test for full download-to-csv flow in tests/test_preprocess.py::test_full_pipeline_sample"

# Launch all implementation tasks for US1 that are independent:
Task: "Implement download_data.py: Download stratified sample"
Task: "Implement download_data.py: Verify checksums"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify `aligned_dataset.csv`)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Model comparison)
4. Add User Story 3 → Test independently → Deploy/Demo (Interpretability)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data)
   - Developer B: User Story 2 (Modeling) - *Can start once T020 (aligned_dataset.csv) is done*
   - Developer C: User Story 3 (Interpretability) - *Can start once T026 (model saved) is done*
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
- **Constraint**: All tasks must run on CPU-only CI (limited cores, constrained RAM, 6h limit). No GPU, no 8-bit quantization, no large LLMs.
- **Data Scope**: Per plan.md, this project uses OC20 exclusively. External dataset tasks (Materials Project, 2025 CO2 study) are omitted due to data unavailability.