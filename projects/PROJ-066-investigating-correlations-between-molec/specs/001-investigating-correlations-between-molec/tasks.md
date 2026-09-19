# Tasks: Investigating Correlations Between Molecular Descriptors and Drug-Likeness Scores

**Input**: Design documents from `/specs/001-gene-regulation/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-066-investigating-correlations-between-molec/`)
- [X] T002 Initialize Python 3.10+ project with `requirements.txt` dependencies (`rdkit`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn`)
- [ ] T003 [P] Configure linting and formatting tools (black, ruff)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `contracts/` directory with `molecule.schema.yaml` and `model_output.schema.yaml` based on spec requirements
- [X] T005 [P] Create `code/utils/config.py` defining constants: `RANDOM_SEED=42`, `MAX_MEMORY_GB=7`, `MAX_DURATION_HOURS=6`
- [X] T006 [P] Implement `code/utils/logging.py` for structured logging of data pipeline steps
- [X] T007 Create `code/utils/update_state.py` to update `state/projects/PROJ-066-investigating-correlations-between-molec.yaml` with artifact hashes
- [ ] T008 Setup directory structure: `data/raw/`, `data/processed/`, `code/data/`, `code/models/`, `code/utils/`, `tests/`
- [X] T030a [P] Implement memory/time monitoring hooks in `code/utils/config.py` and `code/utils/logging.py` to track resource usage during pipeline execution (SC-004, SC-005)
- [X] T033 [P] Implement the integration interface for state updates: Create the `update_state()` wrapper function in `code/utils/update_state.py` that accepts artifact paths and hashes, and ensure it is ready to be called by downstream tasks (T015, T026). This task builds the mechanism, while T015/T026 will implement the *calls* to it.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download ChEMBL 33, sanitize structures, filter for targets, handle duplicates, and generate a clean dataset.

**Independent Test**: The pipeline can be tested by running the data acquisition script and verifying that the output CSV contains exactly the columns required (SMILES, experimental value, calculated descriptors) with zero rows containing missing values or invalid chemical structures.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Implement `code/data/download.py`: Fetch the latest ChEMBL SQLite dataset via FTP. Validate the downloaded file's checksum against the official source, and **record this checksum in `state/projects/PROJ-066-investigating-correlations-between-molec.yaml`** as required by Constitution Principle III (Data Hygiene) and V (Versioning). Save the raw file to `data/raw/chembl_33.db` (FR-001). **Note**: This task is strictly for downloading 2D descriptor data for correlation analysis, NOT for deep learning or GNNs.
- [X] T010 [US1] Implement `code/data/preprocess.py` -> `sanitize_molecules()`: Use RDKit to remove salts, fix valences, and log/remove invalid structures. **Must handle 'exotic elements' by logging and excluding molecules where RDKit sanitizer fails to correct valence** (FR-002, Edge Case 2). This logic must be atomic within this step.
- [X] T012 [US1] Implement `code/data/preprocess.py` -> `deduplicate_smiles()`: Handle duplicate SMILES by retaining most recent assay date or averaging values if dates match (FR-009, Edge Case 1). **Must run AFTER sanitization (T010) and BEFORE target filtering** to ensure correct record retention.
- [X] T011 [US1] Implement `code/data/preprocess.py` -> `filter_targets()`: Filter for oral bioavailability, apparent permeability (Papp), or clearance; remove rows with missing targets (FR-001, FR-002). **Must run AFTER deduplication** to ensure the 'most recent' entry is kept.
- [X] T013 [US1] Implement `code/data/preprocess.py` -> `sample_dataset`: Perform stratified random sampling on the **filtered dataset** to generate a computationally feasible subset capped at [deferred] molecules. The sampling logic must balance statistical power with resource limits (FR-008, SC-005). **Must run BEFORE descriptor calculation**.
- [X] T014 [US1] Implement `code/data/preprocess.py` -> `calculate_descriptors()`: Compute 2D descriptors (TPSA, logP, MW, rotatable bonds, H-bond donors/acceptors, ring count) for all retained molecules (FR-003)
- [ ] T015 [US1] Implement `code/data/preprocess.py` -> `write_processed_data()`: Output `data/processed/molecules_processed.csv` and validate against `contracts/molecule.schema.yaml` before saving. **Must explicitly call `update_state.py` (from T033) to record the new artifact hash in the state file.**
- [X] T016 [US1] Write unit tests in `tests/test_preprocess.py` for sanitization, deduplication logic, and descriptor calculation accuracy. **Dependency: Must run after T010-T015 implementation.** This task is placed here to group it with the code it validates, ensuring TDD compliance without confusing list-order dependencies on unrelated tasks like T009.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Descriptor Calculation and Model Training (Priority: P2)

**Goal**: Split data, train Linear Regression and Random Forest models, and generate feature importance reports.

**Independent Test**: The modeling step is testable by verifying that the training script outputs two distinct model artifacts (one linear, one tree-based) and a feature importance report, without crashing due to memory constraints on the CPU runner.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/models/train.py` -> `split_data()`: Load `molecules_processed.csv`, perform stratified train/test split (seed=42) by target variable (FR-004)
- [ ] T018 [US2] Implement `code/models/train.py` -> `train_linear_regression()`: Fit Linear Regression model on training set; save artifact to `data/processed/model_lr.pkl` (FR-005)
- [ ] T019 [US2] Implement `code/models/train.py` -> `train_random_forest()`: Fit Random Forest model on training set with memory-conscious parameters (max_depth, n_estimators) for CPU runner; **include memory profiling hooks**; save artifact to `data/processed/model_rf.pkl` (FR-005)
- [ ] T020 [US2] Implement `code/models/train.py` -> `generate_feature_importance()`: Extract and rank feature importances from Random Forest; save report to `data/processed/feature_importance.json` (FR-005)
- [ ] T021 [P] [US2] Write unit tests in `tests/test_models.py` for model training success, artifact loading, and memory usage checks

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Evaluation and Visualization (Priority: P3) & Validation

**Goal**: Evaluate models on test set, calculate metrics (RMSE, r), and generate visualizations. **Also includes mandatory resource constraint verification.**

**Independent Test**: The evaluation step is testable by running the script on the test set and verifying that the output includes specific numerical metrics (RMSE, r) and that the generated PNG files are non-empty and correctly labeled.

### Implementation for User Story 3

- [ ] T022 [US3] Implement `code/models/evaluate.py` -> `calculate_metrics()`: Load test set and models; compute RMSE and Pearson correlation coefficient (r) for both models; print results (FR-006, SC-001, SC-002)
- [ ] T023 [US3] Implement `code/models/evaluate.py` -> `baseline_comparison()`: Compute RMSE against a mean predictor baseline. **Must explicitly write this baseline RMSE to `metrics_summary.json` and print it** to satisfy SC-002 (SC-002)
- [ ] T024 [US3] Implement `code/models/evaluate.py` -> `plot_predicted_vs_experimental()`: Generate scatter plot of predicted vs. experimental values; save as `data/processed/plot_scatter.png` (FR-007)
- [ ] T025 [US3] Implement `code/models/evaluate.py` -> `plot_feature_importance()`: Generate bar chart of feature importances; save as `data/processed/plot_importance.png` (FR-007, SC-003)
- [ ] T026 [US3] Implement `code/models/evaluate.py` -> `save_metrics_summary()`: Write final metrics (including baseline RMSE from T023) and plot paths to `data/processed/metrics_summary.json` and validate against `contracts/model_output.schema.yaml`. **Must explicitly call `update_state.py` (from T033) to record the new artifact hashes in the state file.** (FR-006, SC-002)
- [ ] T027 [P] [US3] Write integration tests in `tests/test_models.py` for end-to-end evaluation pipeline and visualization generation

### Validation & Resource Gates (Mandatory)

- [ ] T034 [P] Run full pipeline verification: Execute the complete pipeline from download to visualization. **Must capture pipeline execution time and peak memory usage programmatically**, writing these values to `metrics_summary.json` and the project state file. Verify the pipeline completes within 6 hours and <7GB RAM peak. **This is a mandatory gate, not optional optimization** (SC-004, SC-005, Constitution Principle VII)

**Checkpoint**: All user stories should now be independently functional, and resource constraints verified.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T035 [P] Documentation updates: Ensure `quickstart.md` explains how to run the full pipeline from download to visualization
- [ ] T036 Code cleanup: Refactor `code/data/preprocess.py` and `code/models/train.py` for modularity and readability
- [ ] T037 [P] Run `pytest` suite to ensure all tests pass
- [ ] T038 Run quickstart.md validation to confirm end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Validation (Phase 5)**: Depends on all desired user stories being complete
- **Polish (Final Phase)**: Depends on Validation passing

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - *Note*: T009 (Download) must complete before T010 (Sanitize)
 - *Note*: T012 (Deduplicate) must complete before T011 (Filter Targets)
 - *Note*: T013 (Sample) must complete before T014 (Descriptors)
 - *Note*: T015 (Write Processed) must complete before T017 (Split Data)
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`molecules_processed.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (Model artifacts)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (N/A for data science, but data loading before processing)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch data download and config setup together:
Task: "Fetch ChEMBL Release 33 SQLite via FTP (T009)"
Task: "Create code/utils/config.py (T005)"

# Once data is present, launch sanitization and deduplication:
Task: "Implement sanitize_molecules (T010)"
Task: "Implement deduplicate_smiles (T012)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Pipeline)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify clean CSV output)
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Evaluation)
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
- **Data Integrity**: Ensure `code/data/download.py` fails loudly if ChEMBL FTP is unreachable; do not generate synthetic data.
- **Memory Safety**: Monitor `code/data/preprocess.py` and `code/models/train.py` to ensure they respect the 7GB RAM limit. **T013 and T019 must include explicit memory checks.**
- **Resource Gates**: T034 is a mandatory gate; the project cannot proceed to polish if resource limits are exceeded.
- **State Updates**: T033 provides the integration mechanism; T015 and T026 must explicitly invoke it to record artifact hashes.