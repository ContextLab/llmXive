# Tasks: Predicting Solubility in Mixed Solvents with Machine Learning

**Input**: Design documents from `/specs/001-predicting-solubility-mixed-solvents/`
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

- [ ] T001 Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `data/artifacts/`, `tests/`, `specs/001-predicting-solubility-in-mixed-solvents/contracts/`
- [ ] T002 Create Python 3.11 virtual environment and pinned dependency file: `code/requirements.txt`
- [ ] T003 [P] Create linting and formatting configuration files: `.flake8` and `pyproject.toml` (with `[tool.black]` section)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/utils/constants.py` containing fixed random seeds (numpy, pandas, sklearn, xgboost) and standard file paths
- [ ] T005 Create `code/utils/logging.py` implementing memory/disk monitoring: logs to stderr and exits with a non-zero status code if usage exceeds specified thresholds for RAM or disk.
- [ ] T006 Create data directory structure: `data/raw/`, `data/processed/`, `data/artifacts/`
- [ ] T006b Create `code/utils/checksums.py` to generate `data/.checksums.json`
- [ ] T007 Create schema definition files: `specs/001-predicting-solubility-in-mixed-solvents/contracts/solubility_record.schema.yaml` and `specs/001-predicting-solubility-in-mixed-solvents/contracts/processed_dataset.schema.yaml`
- [ ] T008 Create `code/utils/errors.py` defining `CustomDataError`, `MissingURLError`, and `InvalidStoichiometryError`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw solubility data from verified EPA sources (DSSTox excluded per Plan/Spec amendment), filter for MW < 500 Da, compute RDKit descriptors, and generate composition-weighted solvent descriptors.

**Independent Test**: The pipeline can be tested by running the data processing script on a small subset of the input files and verifying that the output CSV contains the expected columns (solute SMILES, solvent descriptors, mixture composition, calculated interaction terms) and that the row count matches the filtered dataset size.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Create `tests/contract/test_schema_validation.py` containing function `test_solubility_record_valid` for schema validation
- [ ] T010 [P] [US1] Create `tests/integration/test_pipeline.py` containing function `test_ingest_sample` for data ingestion integration testing

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/01_data_ingestion.py`: fetch EPA data (DSSTox excluded per Plan) and filter for molecules with MW < 500 Da
- [ ] T012 [US1] Implement composition validation in `code/01_data_ingestion.py`: reject or normalize rows where composition sum != 1.0 (within tolerance) and write filtered data to `data/processed/cleaned_compositions.csv`
- [ ] T013 [US1] Implement KNN imputation for missing solvent properties in `code/01_data_ingestion.py`; drop rows if imputation fails; log imputation rate to `data/artifacts/imputation_log.txt` and write cleaned data to `data/processed/imputed_data.csv` (target <15%)
- [ ] T014 [US1] Implement `code/02_feature_engineering.py` to compute Morgan fingerprints and topological indices using RDKit
- [ ] T015 [US1] Implement composition-weighted solvent descriptor calculation in `code/02_feature_engineering.py` (weighted average of properties * mole fractions)
- [ ] T016 [US1] Implement explicit interaction term generation (polynomial, ratio) in `code/02_feature_engineering.py` **IF** mixed-solvent data exists; otherwise, apply to pure solvent descriptors; append columns to `data/processed/solubility_features.csv`
- [ ] T017 [US1] Implement pivot logic in `code/02_feature_engineering.py`: if mixed-solvent entries < 100, flag dataset as "Pure Solvent", drop the "non-linear mixing" hypothesis per Plan, write `data/artifacts/pivot_decision.json`, and trigger re-scoping of US2/US3 tasks
- [ ] T018 [US1] Write final processed dataset to `data/processed/solubility_features.csv` with checksum

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train Gradient Boosting and Random Forest models, compare against Abraham solvation parameter baseline, and perform statistical significance testing.

**Independent Test**: The training pipeline can be tested by executing the training script with a fixed random seed and a small hyperparameter grid, verifying that the output includes trained model artifacts and a comparison report showing RMSE and R² for all approaches.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Create `tests/contract/test_model_artifacts.py` containing function `test_model_artifact_valid` for model artifact validation
- [ ] T020 [P] [US2] Create `tests/integration/test_training.py` containing function `test_training_sample` for training pipeline integration testing

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/03_model_training.py` to train XGBoost and Random Forest regressors with 5-fold cross-validation and hyperparameter grid (limit ≤30 mins/trial)
- [ ] T022 [US2] Implement Abraham solvation parameter model baseline in `code/03_model_training.py`: use `solv` package; if unavailable, implement a linear regression baseline on Abraham parameters manually
- [ ] T023 [US2] Implement evaluation logic in `code/04_evaluation.py` to calculate RMSE, MAE, and R² for all models on hold-out test set
- [ ] T024 [US2] Implement paired t-test on absolute errors per Constitution Principle VII (overriding Spec FR-005 Wilcoxon) in `code/04_evaluation.py`; write statistical test results (p-value, t-statistic) to `data/artifacts/statistical_test_results.json`
- [ ] T025 [US2] Generate comparison report in `data/artifacts/training_report.json` including metrics and statistical significance (p < 0.05)
- [ ] T026 [US2] Verify runtime and memory usage against CI limits (≤6h, ≤7GB RAM) during training; log warning to `data/artifacts/resource_monitor.log` and abort if exceeded (per FR-008)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Interaction Term Analysis (Priority: P3)

**Goal**: Visualize feature importances (SHAP values), identify top interaction terms, and perform sensitivity analysis on SHAP thresholds.

**Independent Test**: The analysis can be tested by generating SHAP summary plots and feature importance tables from the trained best-performing model, verifying that specific interaction terms are ranked and visualized.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Create `tests/contract/test_shap_output.py` containing function `test_shap_format_valid` for SHAP output format validation
- [ ] T028 [P] [US3] Create `tests/integration/test_sensitivity.py` containing function `test_sensitivity_sample` for sensitivity analysis integration testing

### Implementation for User Story 3

- [ ] T029 [US3] Implement SHAP value computation for the best-performing model in `code/04_evaluation.py`
- [ ] T030 [US3] Generate SHAP summary plot and feature importance table in `data/artifacts/shap_analysis.png` and `shap_ranking.json`
- [ ] T031 [US3] Filter and rank top 5 interaction terms contributing to model variance; append to `data/artifacts/shap_ranking.json`
- [ ] T032 [US3] Implement sensitivity analysis in `code/04_evaluation.py`: identify top-ranked terms at thresholds {0.01, 0.05, 0.1}
- [ ] T033 [US3] Calculate Jaccard similarity between top-5 term sets at different thresholds; report minimum Jaccard similarity (target ≥0.6 per SC-004); append metrics to `data/artifacts/shap_ranking.json`
- [ ] T034 [US3] Calculate Spearman rank correlation of SHAP values across CV folds to verify stability (target >0.8 per SC-002); compare result against threshold and record pass/fail; append to `data/artifacts/shap_ranking.json`
- [ ] T035 [US3] Generate final research report in `data/artifacts/final_report.md` containing RMSE, R², p-values, and top interaction terms

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Update `research.md`: append verified source URLs and pivot decisions to the "Data Sources" section
- [ ] T037 Ensure type hints are added to `code/utils/*.py` and remove unused imports
- [ ] T038 Refactor `code/02_feature_engineering.py` to use batch processing for RDKit calls, targeting a [deferred] runtime reduction
- [ ] T039 [P] Add `tests/unit/test_edge_cases.py` containing functions `test_missing_data_handling` and `test_small_dataset_split`
- [ ] T040 Execute `quickstart.md` and record the exit code and any errors in `data/artifacts/quickstart_validation.log`

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
Task: "Create tests/contract/test_schema_validation.py containing function test_solubility_record_valid"
Task: "Create tests/integration/test_pipeline.py containing function test_ingest_sample"

# Launch all models for User Story 1 together:
Task: "Implement composition validation: write filtered data to data/processed/cleaned_compositions.csv"
Task: "Implement KNN imputation: log rate to data/artifacts/imputation_log.txt and write data to data/processed/imputed_data.csv"
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
- **Critical Constraint**: No synthetic data generation. If mixed-solvent data is insufficient, pivot to pure solvent prediction and implement interaction terms for pure solvents.
- **Critical Constraint**: Constitution Principle VII (Paired t-test) takes precedence over Spec FR-005 (Wilcoxon).
- **Critical Constraint**: All tasks must run on CPU-only CI (minimal core count, limited RAM, 14GB disk).
- **Critical Constraint**: DSSTox ingestion is excluded per Plan/Spec amendment; EPA-only data is used.