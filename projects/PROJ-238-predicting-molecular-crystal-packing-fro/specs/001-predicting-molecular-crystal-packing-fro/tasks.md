# Tasks: Predicting Molecular Crystal Packing from Structural Descriptors

**Input**: Design documents from `/specs/001-predicting-crystal-packing/`
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

- [ ] T001.1 Create repository root directories: `code/`, `data/`, `results/`, `state/`
- [ ] T001.2 Create `code/utils/` and `code/tests/` subdirectories
- [ ] T001.3 Create `data/raw/`, `data/descriptors/`, `data/processed/` subdirectories
- [ ] T001.4 Create `results/` and `state/projects/PROJ-238.../` subdirectories
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pins: `rdkit==2023.9.1`, `scikit-learn==1.3.0`, `pandas`, `numpy`, `requests`, `pytest`, `matplotlib`, `seaborn`)
- [ ] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `utils/data_loaders.py` to fetch sample COD CIFs from official bulk URL ` certificate verify failed: Hostname mismatch, certificate is not valid for 'ftp.crystallography.net'. (_ssl.c:1016)")))].
 - **Deliverable**: Generate `data/raw/sample_cifs.txt` containing a set of valid CIF IDs.
 - **Verification**: Verify file exists and contains a sufficient number of lines.
- [ ] T004.1 [P] Validate data volume: Fetch and count valid organic small molecules from COD to ensure N >= 1,000.
 - **Deliverable**: Generate `data/raw/volume_validation.log` with the count.
 - **Verification**: If count < 1,000, the task MUST fail and block Phase 1 execution. Log the count and reason for blocking.
- [ ] T005 [P] Implement `utils/descriptors.py` wrapper for RDKit.
 - **Signature**: `compute_descriptors(mol) -> dict` returning Volume, Surface Area, Dipole, HBA, HBD, PSA.
 - **Verification**: Run on benzene molecule; verify returned Volume is within expected range.
- [ ] T006 [P] Implement `utils/metrics.py` for statistical tests.
 - **Functions**: `paired_t_test(pred1, pred2)`, `bonferroni_correct(p_values, n_comparisons)`, `ks_test(data1, data2)`.
 - **Verification**: Unit tests for each function with known inputs/outputs.
- [ ] T007 [P] Create base data model classes in `code/models.py`.
 - **Classes**: `Molecule` (attrs: id, mw, descriptors), `CrystalStructure` (attrs: id, unit_cell, interaction_type), `ModelResult` (attrs: model_type, metrics, params).
- [ ] T008 [P] Configure environment variables and logging infrastructure in `code/config.py`.
 - **Env Vars**: `COD_URL`, `RANDOM_SEED`, `DATA_PATH`.
 - **Format**: JSON logs to stdout.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw crystal structure data from COD, filter for valid organic small molecules, compute standardized molecular descriptors, and derive the `packing_coefficient` target.

**Independent Test**: Run `code/01_ingest_and_descriptors.py` on a sample of COD entries; verify output CSV contains non-null values for all 6 descriptors and the derived `packing_coefficient`.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for CIF parsing logic in `tests/unit/test_data_loaders.py`
- [ ] T010 [P] [US1] Unit test for descriptor computation (RDKit) in `tests/unit/test_descriptors.py`
- [ ] T011 [P] [US1] Integration test for full ingestion pipeline with sample data in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/01_ingest_and_descriptors.py` to download CIFs, parse unit cell parameters ($a, b, c, \alpha, \beta, \gamma$), and calculate $V_{cell}$.
 - **Deliverable**: Generate `data/descriptors/raw_descriptors.csv` with columns [ID, Volume, SurfaceArea,...].
 - **Verification**: Verify rows exist.
- [ ] T013 [US1] Implement logic to add missing hydrogens geometrically before descriptor calculation; log count of entries modified.
- [ ] T014 [US1] Implement descriptor computation for Volume, Surface Area, Dipole, HBA, HBD, PSA using `utils/descriptors.py`.
- [ ] T015 [US1] Implement logic to derive `packing_coefficient` = $V_{mol} / V_{cell}$ and filter out physically impossible values ($<0.5$ or $>1.0$).
 - **Verification**: Log the count of filtered entries to stdout.
- [ ] T016 [US1] Implement missing data handling: impute auxiliary descriptors (e.g., Dipole) with training set median; exclude rows with missing target; log counts.
- [ ] T017 [US1] Implement stratified split by `packing_coefficient` (target) into Train/Val/Test.
 - **Note**: This supersedes Spec FR-003 (molecular weight) which contradicts the Plan's scientific requirement to prevent target drift.
 - **Deliverable**: Generate `data/processed/train.csv`, `data/processed/val.csv`, `data/processed/test.csv` and `data/processed/split_report.json`.
 - **Verification**: Assert KS distance < 0.05 across splits for the target variable in `split_report.json`.
- [ ] T017.1 [US1] Verify Molecular Weight distribution across splits.
 - **Verification**: Run KS test on MW across splits; log result. If KS > 0.05, log a warning but do not block (secondary check).
- [ ] T018 [US1] Generate SHA-256 checksums for raw CIFs and derived CSVs; record in `state/projects/PROJ-238.../artifact_hashes`.
- [ ] T019 [US1] Extract geometric criteria from CIFs to classify dominant interaction types (H-bond: distance < 3.5Å and angle > 150°).
 - **Deliverable**: Add columns `interaction_type`, `confidence` to `data/descriptors/derived.csv`.
 - **Verification**: Verify all rows in `derived.csv` have a non-null `interaction_type`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting regressors to predict `packing_coefficient` and compare performance against a mean-predictor baseline with statistical rigor.

**Independent Test**: Execute training pipeline on training set, evaluate on test set, verify Random Forest achieves statistically significant improvement over mean baseline (p < 0.05).

### Tests for User Story 2

- [ ] T020 [P] [US2] Unit test for model training convergence within 30 mins on 2-CPU in `tests/unit/test_training.py`
- [ ] T021 [P] [US2] Integration test for paired t-test against mean baseline in `tests/integration/test_model_evaluation.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/02_train_models.py` to load pre-split data from `data/processed/`.
 - **Deliverable**: Load `train.csv`, `val.csv`, `test.csv`. Verify they exist with non-overlapping indices.
- [ ] T023 [US2] Train Random Forest regressor with default hyperparameters and `random_state=42`.
- [ ] T024 [US2] Train Gradient Boosting regressor with default hyperparameters and `random_state=42`.
- [ ] T025 [US2] Implement Mean Predictor baseline.
- [ ] T026 [US2] Implement Control Analysis: Train secondary RF/GB models excluding Volume and Surface Area to test if interaction descriptors drive packing.
 - **Deliverable**: Save results to `results/control_analysis_metrics.json`.
- [ ] T027 [US2] Evaluate models using R², MAE, RMSE on test set.
- [ ] T028 [US2] Perform paired t-test (Model vs Baseline) and apply Bonferroni correction.
 - **Logic**: Calculate alpha_corrected = 0.05 / N_models (where N_models includes RF, GB, and Control Analysis).
 - **Verification**: Log the corrected alpha and p-values.
- [ ] T029 [US2] Save metrics to `results/metrics.json` including R², MAE, p-values, and correction flag.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance, Sensitivity Analysis, and Interaction Classification (Priority: P3)

**Goal**: Identify influential descriptors, perform sensitivity analysis, and classify dominant intermolecular interaction types using geometric criteria.

**Independent Test**: Generate feature importance plot, sensitivity report showing R² stability, and classification report with bootstrapped confidence intervals.

### Tests for User Story 3

- [ ] T030 [P] [US3] Unit test for permutation importance calculation in `tests/unit/test_feature_importance.py`
- [ ] T031 [P] [US3] Unit test for LOFO sensitivity analysis in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement `code/03_evaluate_and_report.py` to calculate Permutation Importance (not Gini) for the trained Random Forest.
- [ ] T033 [US3] Generate `results/feature_importance.png` identifying top 3 features and cumulative importance.
- [ ] T034 [US3] Perform Leave-One-Feature-Out (LOFO) analysis; document R² variation across feature subsets in `results/sensitivity_report.md`.
- [ ] T035 [US3] Read interaction labels from `data/descriptors/derived.csv` (pre-calculated in T019) to generate interaction classification report.
 - **Deliverable**: Generate `results/interaction_classification.md` with accuracy and confidence intervals.
 - **Verification**: Verify the report uses the pre-calculated labels and does not re-process raw CIFs.
- [ ] T036 [US3] Evaluate interaction classification accuracy and compute confidence intervals via bootstrapping.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Update `state/projects/PROJ-238.../artifact_hashes` with final result checksums
- [ ] T038 Verify `results/metrics.json` contains all required fields and Bonferroni flag
- [ ] T039 [P] Generate `quickstart.md` and `contracts/` schemas from data model
- [ ] T040 [P] Execute full pipeline validation: Run `code/01_ingest_and_descriptors.py`, `code/02_train_models.py`, and `code/03_evaluate_and_report.py` in a CI environment.
 - **Verification**: Verify all exit codes are 0 and artifacts are generated in `data/` and `results/`.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on models from US2

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
Task: "Unit test for CIF parsing logic in tests/unit/test_data_loaders.py"
Task: "Unit test for descriptor computation (RDKit) in tests/unit/test_descriptors.py"
Task: "Integration test for full ingestion pipeline with sample data in tests/integration/test_ingestion.py"

# Launch all implementation tasks for User Story 1 together (where file paths differ):
Task: "Implement code/01_ingest_and_descriptors.py to download CIFs..."
Task: "Implement logic to add missing hydrogens geometrically..."
Task: "Implement descriptor computation for Volume, Surface Area..."
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