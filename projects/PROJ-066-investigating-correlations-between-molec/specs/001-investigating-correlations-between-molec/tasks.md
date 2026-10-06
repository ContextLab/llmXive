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

- [ ] T001a [P] Create `projects/PROJ-066-investigating-correlations-between-molec/README.md` with project overview and quickstart instructions.
- [ ] T003a [P] Create `projects/PROJ-066-investigating-correlations-between-molec/code/pyproject.toml` with Black configuration (line-length 88, target-version py310).
- [ ] T003b [P] Create `projects/PROJ-066-investigating-correlations-between-molec/code/.ruff.toml` with linting rules (max-line-length 88, ignore E501).
- [ ] T004a [P] Create `projects/PROJ-066-investigating-correlations-between-molec/code/contracts/molecule.schema.yaml` defining the schema for processed molecular data (SMILES, descriptors, target).
- [ ] T004b [P] Create `projects/PROJ-066-investigating-correlations-between-molec/code/contracts/model_output.schema.yaml` defining the schema for model metrics and feature importance.
- [ ] T008a [P] Create `projects/PROJ-066-investigating-correlations-between-molec/data/raw/` directory.
- [ ] T008b [P] Create `projects/PROJ-066-investigating-correlations-between-molec/data/processed/` directory.
- [ ] T008c [P] Create `projects/PROJ-066-investigating-correlations-between-molec/code/data/` directory.
- [ ] T008d [P] Create `projects/PROJ-066-investigating-correlations-between-molec/code/models/` directory.
- [ ] T008e [P] Create `projects/PROJ-066-investigating-correlations-between-molec/tests/` directory.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create `projects/PROJ-066-investigating-correlations-between-molec/code/utils/config.py` defining constants: `RANDOM_SEED=42`, `MAX_MEMORY_GB=7`, `MAX_DURATION_HOURS=6`. **Explicitly document that `RANDOM_SEED` must be passed to the stratified splitter in T017 to ensure reproducibility.**
- [ ] T006 [P] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/utils/logging.py` for structured logging of data pipeline steps.
- [ ] T007 [P] Create `projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py` to update `state/projects/PROJ-066-investigating-correlations-between-molec.yaml` with artifact hashes.
- [ ] T030a [P] Implement memory/time monitoring hooks in `projects/PROJ-066-investigating-correlations-between-molec/code/utils/config.py` and `projects/PROJ-066-investigating-correlations-between-molec/code/utils/logging.py` to track resource usage during pipeline execution (SC-004, SC-005).
- [ ] T033 [P] Implement the integration interface for state updates: Create the `update_state()` wrapper function in `projects/PROJ-066-investigating-correlations-between-molec/code/utils/update_state.py` that accepts artifact paths and hashes, and ensure it is ready to be called by downstream tasks (T015, T026). This task builds the mechanism, while T015/T026 will implement the *calls* to it.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel (once T004a/b, T008a-e, T003a/b, T001a complete)

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download ChEMBL 33, sanitize structures, filter for targets, handle duplicates, and generate a clean dataset.

**Independent Test**: The pipeline can be tested by running the data acquisition script and verifying that the output CSV contains exactly the columns required (SMILES, experimental value, calculated descriptors) with zero rows containing missing values or invalid chemical structures.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/data/download.py`: Fetch the latest available release of ChEMBL via FTP. **URL**: `ftp://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_33/`. **Format**: Download the compressed archive (`.tar.gz` or `.zip`) containing the SQLite database, NOT a raw `.db` file. **Extraction**: Extract the archive to reveal the internal SQLite database file. **Checksum**: Download `chembl_33.sha256` from the same directory, validate SHA-256 of the archive, and **record the verified checksum into `projects/PROJ-066-investigating-correlations-between-molec/state/projects/PROJ-066-investigating-correlations-between-molec.yaml`** (Constitution Principle III). **FAIL LOUDLY**: Raise exception if FTP fails, checksum mismatch, or extraction fails; NO synthetic fallback. **Save to** `projects/PROJ-066-investigating-correlations-between-molec/data/raw/chembl_33.db` (after extraction). **BLOCKED BY**: None.
- [ ] T010 [US1] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/data/preprocess.py` -> `sanitize_molecules()`: Use RDKit to remove salts, fix valences, and log/remove invalid structures. **Must handle 'exotic elements' by logging and excluding molecules where RDKit sanitizer fails**. **BLOCKED BY T009**.
- [ ] T011 [US1] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/data/preprocess.py` -> `filter_targets()`: Filter for oral bioavailability, apparent permeability (Papp), or clearance; remove rows with missing targets (FR-001, FR-002). **Must run AFTER sanitization (T010) and BEFORE deduplication (T012)** to ensure deduplication logic applies only to relevant targets. **BLOCKED BY T009**.
- [ ] T012 [US1] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/data/preprocess.py` -> `deduplicate_smiles()`: Handle duplicate SMILES by retaining most recent assay date or averaging values if dates match (FR-009). **Must run AFTER target filtering (T011)** so that 'most recent assay date' logic applies only to the specific targets of interest. **BLOCKED BY T009, T011**.
- [ ] T013 [US1] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/data/preprocess.py` -> `sample_dataset`: Perform stratified random sampling on the filtered dataset. **Logic**: Start with `target_size = min(scalable_limit, available_rows)`, where `scalable_limit` represents a predefined maximum threshold for dataset size. **Safety Check**: Estimate memory usage for `target_size`. If estimated usage > 6GB (safe buffer), **halve `target_size` and re-estimate**. Repeat halving until estimated usage fits within 6GB. **Edge Case**: If `len(sampled_df) < 100` after reduction, **raise `DataInsufficiencyError("Data Insufficiency: Sample size < 100")` and halt execution immediately**. **BLOCKED BY T009, T012**.
- [ ] T014 [US1] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/data/preprocess.py` -> `calculate_descriptors()`: Compute 2D descriptors (TPSA, logP, MW, rotatable bonds, H-bond donors/acceptors, ring count) for all retained molecules (FR-003). **BLOCKED BY T009, T013**.
- [ ] T015 [US1] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/data/preprocess.py` -> `write_processed_data()`: Output `projects/PROJ-066-investigating-correlations-between-molec/data/processed/molecules_processed.csv`. **Validation**: **Validate EACH row against `projects/PROJ-066-investigating-correlations-between-molec/code/contracts/molecule.schema.yaml` (T004a) DURING the write loop** before writing to disk to prevent invalid artifacts (Plan.md Contract Validation Mapping). **State Update**: **Must explicitly call `update_state.py` (from T033) to record the new artifact hash**. **BLOCKED BY T009, T014**.
- [ ] T016 [US1] Write unit tests in `projects/PROJ-066-investigating-correlations-between-molec/tests/test_preprocess.py` for sanitization, deduplication logic, and descriptor calculation accuracy. **Dependency: Must run after T010-T015 implementation**.

**Checkpoint**: Blocked until T009 (Download) and T004a (Schema) complete. User Story 1 is NOT functional until then.

---

## Phase 4: User Story 2 - Descriptor Calculation and Model Training (Priority: P2)

**Goal**: Split data, train Linear Regression and Random Forest models, and generate feature importance reports.

**Independent Test**: The modeling step is testable by verifying that the training script outputs two distinct model artifacts (one linear, one tree-based) and a feature importance report, without crashing due to memory constraints on the CPU runner.

### Implementation for User Story 2

- [ ] T017 [US2] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/models/train.py` -> `split_data()`: Load `molecules_processed.csv`, perform stratified train/test split (seed=42) by target variable (FR-004). **Use `RANDOM_SEED` from `config.py` (T005)**. **BLOCKED BY T015**.
- [ ] T018 [US2] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/models/train.py` -> `train_linear_regression()`: Fit Linear Regression model on training set; save artifact to `projects/PROJ-066-investigating-correlations-between-molec/data/processed/model_lr.pkl` using **joblib** (scikit-learn version pinned in `requirements.txt`). **BLOCKED BY T017**.
- [ ] T019 [US2] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/models/train.py` -> `train_random_forest()`: Fit Random Forest model on training set with memory-conscious parameters (max_depth, n_estimators) for CPU runner; **include memory profiling hooks**; save artifact to `projects/PROJ-066-investigating-correlations-between-molec/data/processed/model_rf.pkl` using **joblib** (scikit-learn version pinned in `requirements.txt`). **BLOCKED BY T017**.
- [ ] T020 [US2] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/models/train.py` -> `generate_feature_importance()`: Extract and rank feature importances from Random Forest; save report to `projects/PROJ-066-investigating-correlations-between-molec/data/processed/feature_importance.json` (FR-005). **BLOCKED BY T019**.
- [ ] T021 [P] [US2] Write unit tests in `projects/PROJ-066-investigating-correlations-between-molec/tests/test_models.py` for model training success, artifact loading, and memory usage checks.

**Checkpoint**: Blocked until T018 and T019 (Model Training) complete. User Story 2 is NOT functional until then.

---

## Phase 5: User Story 3 - Model Evaluation and Visualization (Priority: P3) & Validation

**Goal**: Evaluate models on test set, calculate metrics (RMSE, r), and generate visualizations. **Also includes mandatory resource constraint verification.**

**Independent Test**: The evaluation step is testable by running the script on the test set and verifying that the output includes specific numerical metrics (RMSE, r) and that the generated PNG files are non-empty and correctly labeled.

### Implementation for User Story 3

- [ ] T022 [US3] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/models/evaluate.py` -> `calculate_metrics()`: Load test set and models; compute RMSE and Pearson correlation coefficient (r) for both models; print results (FR-006, SC-001, SC-002). **BLOCKED BY T018, T019**.
- [ ] T023 [US3] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/models/evaluate.py` -> `baseline_comparison()`: Compute RMSE against a mean predictor baseline. **Logic**: Calculate mean of training set target values; compute RMSE of this mean against test set. **Output**: **Print the mean predictor baseline RMSE to the console/stdout** (SC-002) AND write to `metrics_summary.json` under key `mean_predictor_rmse`. **Validation**: Must verify `metrics_summary.json` contains `mean_predictor_rmse` key before task completion. **BLOCKED BY T018, T019**.
- [ ] T024 [US3] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/models/evaluate.py` -> `plot_predicted_vs_experimental()`: Generate scatter plot of predicted vs. experimental values; save as `projects/PROJ-066-investigating-correlations-between-molec/data/processed/plot_scatter.png` (FR-007). **BLOCKED BY T018, T019**.
- [ ] T025 [US3] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/models/evaluate.py` -> `plot_feature_importance()`: Generate bar chart of feature importances; save as `projects/PROJ-066-investigating-correlations-between-molec/data/processed/plot_importance.png` (FR-007, SC-003). **BLOCKED BY T020**.
- [ ] T026 [US3] Implement `projects/PROJ-066-investigating-correlations-between-molec/code/models/evaluate.py` -> `save_metrics_summary()`: Write final metrics (including baseline RMSE from T023) and plot paths to `projects/PROJ-066-investigating-correlations-between-molec/data/processed/metrics_summary.json`. **JSON Schema**: `{baseline_rmse, model_lr_rmse, model_rf_rmse, model_lr_r, model_rf_r, pipeline_time_seconds, peak_memory_mb, plot_scatter_path, plot_importance_path}`. Validate against `projects/PROJ-066-investigating-correlations-between-molec/code/contracts/model_output.schema.yaml`. **Must explicitly call `update_state.py` (from T033) to record the new artifact hashes**. **BLOCKED BY T018, T019, T023, T024, T025**.
- [ ] T027 [P] [US3] Write integration tests in `projects/PROJ-066-investigating-correlations-between-molec/tests/test_models.py` for end-to-end evaluation pipeline and visualization generation.

### Validation & Resource Gates (Mandatory)

- [ ] T034 [P] Run full pipeline verification: Execute the complete pipeline **excluding the download step** (start from `molecules_processed.csv` post-T015) to measure time and memory. **Method**: Use `time.perf_counter()` for duration (seconds) and `psutil.Process().memory_info().rss` for peak memory (convert to MB). **Input**: Capture values from monitoring hooks implemented in T030a. **Scope**: **DO NOT download the raw ChEMBL archive**; verify only the processing, modeling, and evaluation steps. **Output**: Write these values to `metrics_summary.json` (keys: `pipeline_time_seconds`, `peak_memory_mb`). Verify pipeline completes within 6 hours and <7GB RAM peak. **BLOCKED BY T015, T018, T019, T023, T024, T025**.

**Checkpoint**: Blocked until T018, T019, and T026 complete. User Story 3 is NOT functional until then.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T035 [P] Documentation updates: Ensure `quickstart.md` explains how to run the full pipeline from download to visualization.
- [ ] T036 [P] Code cleanup: Refactor `projects/PROJ-066-investigating-correlations-between-molec/code/data/preprocess.py` and `projects/PROJ-066-investigating-correlations-between-molec/code/models/train.py` for modularity and readability.
- [ ] T037 [P] Run `pytest` suite to ensure all tests pass.
- [ ] T038 [P] Run quickstart.md validation to confirm end-to-end reproducibility.

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
 - *Note*: T010 (Sanitize) must complete before T011 (Filter Targets)
 - *Note*: T011 (Filter Targets) must complete before T012 (Deduplicate)
 - *Note*: T012 (Deduplicate) must complete before T013 (Sample)
 - *Note*: T013 (Sample) must complete before T014 (Descriptors)
 - *Note*: T014 (Descriptors) must complete before T015 (Write Processed)
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

# Once data is present, launch sanitization and filtering:
Task: "Implement sanitize_molecules (T010)"
Task: "Implement filter_targets (T011)"
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
- **Memory Safety**: Monitor `code/data/preprocess.py` and `code/models/train.py` to ensure they respect the 7GB RAM limit. **T013 and T019 must include explicit memory checks with a halving fallback strategy.**
- **Resource Gates**: T034 is a mandatory gate; the project cannot proceed to polish if resource limits are exceeded. **T034 must run on processed data only, not raw download.**
- **State Updates**: T033 provides the integration mechanism; T015 and T026 must explicitly invoke it to record artifact hashes.
- **Validation Timing**: T015 must validate row-by-row during write, not post-hoc.