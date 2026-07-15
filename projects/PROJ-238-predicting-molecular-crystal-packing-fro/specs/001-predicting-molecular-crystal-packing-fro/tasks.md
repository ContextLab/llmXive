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
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pins: `rdkit==2023.9.1`, `scikit-learn==1.3.0`, `pandas`, `numpy`, `requests`, `pytest`, `matplotlib`, `seaborn`)
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `utils/data_loaders.py` to fetch **only** the canonical COD bulk download URL ` Name or service not known)"))].
 **Constraint**: NO fallback URLs are permitted.
 **Deliverable**: Generate `data/raw/cod_sample_ids.txt` containing a list of COD entry IDs.
 **Verification**: File exists and contains **≥ 100** lines.
- [ ] T004.1 [P] Validate that the COD sample contains at least **[deferred]** valid organic small molecules.
 **Definition of valid**: Molecules with molecular weight < 1000 Da, containing only C/H/N/O/F/Cl/Br atoms (no metals), as determined via RDKit filters.
 **Deliverable**: Write count and any exclusions to `data/raw/volume_validation.log`.
 **Verification**: Log reports count ≥ 1000; otherwise task fails and blocks further phases.
- [X] T005 [P] Implement `utils/descriptors.py` wrapper for RDKit.
 **Signature**: `compute_descriptors(mol) -> dict` returning Volume, Surface Area, Dipole, HBA, HBD, PSA.
 **Verification**: Run on benzene (`c1ccccc1`); assert returned Volume is between **50 Å³** and **150 Å³**.
- [X] T006 [P] Implement `utils/metrics.py` for statistical tests.
 **Functions**: `paired_t_test(pred1, pred2)`, `bonferroni_correct(p_values, n_comparisons)`, `ks_test(data1, data2)`.
 **Verification**: Unit tests with known numeric inputs/outputs (provided in `tests/unit/`).
- [X] T007 [P] Create base data model classes in `code/models.py`.
 **Classes**: `Molecule` (attrs: id, mw, descriptors), `CrystalStructure` (attrs: id, unit_cell, interaction_type), `ModelResult` (attrs: model_type, metrics, params).
- [X] T008 [P] Configure environment variables and logging infrastructure in `code/config.py`.
 **Env Vars**: `COD_URL`, `RANDOM_SEED`, `DATA_PATH`.
 **Format**: JSON logs to stdout.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw crystal structure data from COD, filter for valid organic small molecules, compute standardized molecular descriptors, and derive the `packing_coefficient` target.

**Independent Test**: Run `code/01_ingest_and_descriptors.py` on a sample of COD entries; verify output CSV contains non‑null values for all 6 descriptors and the derived `packing_coefficient`.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for CIF parsing logic in `tests/unit/test_data_loaders.py`
- [ ] T010 [P] [US1] Unit test for descriptor computation (RDKit) in `tests/unit/test_descriptors.py`
- [ ] T011 [P] [US1] Integration test for full ingestion pipeline with sample data in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/01_ingest_and_descriptors.py` to download CIFs, parse unit cell parameters ($a, b, c, \alpha, \beta, \gamma$), and calculate $V_{cell}$.
 **Deliverable**: Generate `data/descriptors/raw_descriptors.csv` with columns `[ID, Volume, SurfaceArea, Dipole, HBD, HBA, PSA, packing_coefficient]`.
 **Verification**: File exists with **≥ 50** rows and all listed columns present.
- [ ] T013 [US1] Implement logic to add missing hydrogens geometrically before descriptor calculation; log count of modified entries to `data/processed/hydrogen_addition.log`.
- [ ] T014 [US1] Implement descriptor computation for Volume, Surface Area, Dipole, HBA, HBD, PSA using `utils/descriptors.py`. <!-- FAILED: unspecified -->
- [~] T015 [US1] Derive `packing_coefficient = V_mol / V_cell` and **filter out physically impossible values** (`packing_coefficient < 0` or `> 1`).
 **Log**: Write number of excluded rows to `data/processed/filter_log.txt`.
- [ ] T016 [US1] Implement missing‑data handling: impute auxiliary descriptors (e.g., Dipole) with the training‑set median and flag the row in `data/descriptors/raw_descriptors.csv` with a boolean column `dipole_imputed`. Exclude rows with missing target and log count to `data/processed/missing_target.log`.
- [ ] T017.1 [US1] Perform a **stratified split** of the cleaned dataset into Train/Val/Test (70/15/15) **by molecular weight** (MW) to satisfy FR‑003.
 **Deliverable**: `data/processed/train.csv`, `data/processed/val.csv`, `data/processed/test.csv`.
- [ ] T017.2 [US1] Validate the split: run a Kolmogorov‑Smirnov test on the MW distributions across the three splits; assert KS distance `< 0.05`.
 **Log**: Write KS statistic and p‑value to `data/processed/split_validation.log`.
- [ ] T017.3 [US1] Generate a JSON report `data/processed/split_report.json` summarizing row counts, MW statistics (mean, std), and KS test results. Follow the schema defined in `contracts/dataset.schema.yaml`.
- [ ] T017.1‑T017.3 are **not** marked `[P]` because they depend sequentially on each other.
- [~] T018 [US1] Generate SHA‑256 checksums for raw CIFs and all derived CSV/JSON artifacts; record them in `state/projects/PROJ-238.../artifact_hashes`.
- [ ] **(Removed) T019** – interaction classification is now handled in User Story 3.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting regressors to predict `packing_coefficient` and compare performance against a mean‑predictor baseline with statistical rigor.

**Independent Test**: Execute training pipeline on training set, evaluate on test set, verify Random Forest achieves statistically significant improvement over mean baseline (p < 0.05).

### Tests for User Story 2

- [X] T020 [P] [US2] Unit test for model training convergence within 30 mins on 2‑CPU in `tests/unit/test_training.py`
- [X] T021 [P] [US2] Integration test for paired t‑test against mean baseline in `tests/integration/test_model_evaluation.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/02_train_models.py` to load pre‑split data from `data/processed/`.
 **Verification**: Files `train.csv`, `val.csv`, `test.csv` exist, have non‑overlapping IDs, and contain the required columns.
- [~] T023 [US2] Train Random Forest regressor with default hyperparameters and `random_state=42`.
- [~] T024 [US2] Train Gradient Boosting regressor with default hyperparameters and `random_state=42`.
- [~] T025 [US2] Implement Mean Predictor baseline (predicts the training‑set mean of `packing_coefficient`).
- [~] T026 [US2] Implement Control Analysis: train secondary RF/GB models **excluding** Volume and Surface Area descriptors to probe the contribution of interaction‑related features.
 **Deliverable**: Save results to `results/control_analysis_metrics.json`.
- [~] T027 [US2] Evaluate all models on the test set; compute R², MAE, RMSE.
- [~] T028 [US2] Perform paired t‑tests of each primary model (RF, GB) against the baseline.
 **Statistical correction**: Calculate `alpha_corrected = 0.05 / 2` (N_models = 2, excluding control analysis) and apply Bonferroni correction.
 **Output**: Write corrected p‑values, `alpha_corrected`, and a flag indicating significance to `results/metrics.json`.
- [ ] T029 [US2] Save a consolidated metrics summary (R², MAE, RMSE, corrected p‑values, significance flags) to `results/metrics.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance, Sensitivity Analysis, and Interaction Classification (Priority: P3)

**Goal**: Identify influential descriptors, perform sensitivity analysis, and classify dominant intermolecular interaction types using geometric criteria.

**Independent Test**: Generate feature importance plot, sensitivity report showing R² stability, and classification report with bootstrapped confidence intervals.

### Tests for User Story 3

- [X] T030 [P] [US3] Unit test for permutation importance calculation in `tests/unit/test_feature_importance.py`
- [X] T031 [P] [US3] Unit test for LOFO sensitivity analysis in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [X] T032 [US3] Implement `code/03_evaluate_and_report.py` to calculate **Permutation Importance** (not Gini) for the trained Random Forest model.
- [ ] T033 [US3] Generate `results/feature_importance.png` identifying the top 3 features and showing their cumulative importance (> 60 % total).
- [X] T034 [US3] Perform Leave‑One‑Feature‑Out (LOFO) analysis; document R² variation across feature subsets in `results/sensitivity_report.md`.
 **Requirement**: Report that removing the top 5 features changes R² by no more than ±0.02.
- [ ] T035.1 [US3] Extract geometric interaction criteria from the original CIF files (e.g., H‑bond distance < 3.5 Å and angle > 150°) and create a temporary table `data/interactions/raw_interactions.csv`.
 **Verification**: File exists with columns `[CIF_ID, interaction_type, confidence]`.
- [ ] T035.2 [US3] Classify the **dominant intermolecular interaction type** for each crystal using the criteria from T035.1; write results to `data/descriptors/derived.csv` (adds columns `interaction_type`, `interaction_confidence`).
 **Verification**: All rows have non‑null `interaction_type`.
- [ ] T035.3 [US3] Generate `results/interaction_classification.md` reporting overall classification accuracy and 95 % confidence intervals obtained via bootstrapping (≥ 1 000 resamples).
 **Verification**: Report includes accuracy, CI, and number of resamples.
- [ ] T036 [US3] (Optional) Evaluate interaction‑type prediction against any available external benchmark (if present) and log results to `results/interaction_benchmark.log`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Update `state/projects/PROJ-238.../artifact_hashes` with final result checksums
- [ ] T038 Verify `results/metrics.json` contains all required fields and the Bonferroni flag
- [ ] T039 [P] Generate `quickstart.md` and `contracts/` schemas from data model
- [ ] T040 [P] Execute full pipeline validation: Run `code/01_ingest_and_descriptors.py`, `code/02_train_models.py`, and `code/03_evaluate_and_report.py` in a CI environment.
 **Verification**: All exit codes are 0 and artifacts are generated in `data/` and `results/`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion – BLOCKS all user stories
- **User Stories (Phase 3‑5)**: All depend on Foundational phase completion
 - User stories can proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) – No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) – Depends on dataset produced by US 1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) – Depends on trained models from US 2 for feature‑importance steps; interaction‑type extraction uses raw CIFs, which are already available from Phase 2.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL – blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
