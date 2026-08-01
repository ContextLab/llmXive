# Tasks: Predicting Molecular Reactivity Using Graph Neural Networks and Public Databases

**Input**: Design documents from `/specs/001-predicting-molecular-reactivity/`
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

- [ ] T001a [P] Create data directories: `data/raw`, `data/processed`, `data/assets`
- [ ] T001b [P] Create code and artifact directories: `code`, `artifacts`, `tests`
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (pinning `torch`, `rdkit`, `scikit-learn`, `pandas`, `datasets`, `networkx`, `psutil`)
- [ ] T003 [P] Configure linting (flake8/ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/loaders.py` with robust retry logic (exponential backoff) for dataset downloads; **MUST** implement orchestration logic to exit with a clear error code and log the specific failure reason after retries are exhausted, as required by spec Edge Cases.
- [X] T005 [P] Implement `code/utils/graph_utils.py` for molecular graph construction (SMILES → Node/Edge features)
- [X] T006 [P] Implement `code/utils/metrics.py` for MSE, MAE, Pearson R, **Wilcoxon signed-rank test (PRIMARY per Plan.md)**, and **paired t-test (SENSITIVITY per Plan.md)**. **CRITICAL**: This utility must be the single source of truth for statistical tests; T025 will test this utility.
- [X] T007 [P] Create base configuration management (`code/config.py`) for random seeds and device settings (`device='cpu'`)
- [ ] T008 [P] Setup logging infrastructure to write structured logs to `artifacts/logs/` and `artifacts/metrics.json`
- [ ] T009a [P] [FR-008] Download the curated reference set of known reactive substructures from verified source `https://huggingface.co/datasets/chembench/reactive_substructures/resolve/main/reference_set.csv` to `data/raw/reference_substructures_raw.csv`.
- [ ] T009b [P] [FR-008] Verify checksum (SHA-256) of `data/raw/reference_substructures_raw.csv` against the source manifest. <!-- FAILED: unspecified -->
- [ ] T009c [P] [FR-008] Ingest verified data into `data/assets/reference_substructures.csv` with schema validation.
- [ ] T009d [P] [FR-009] Download the external kinetic dataset (≥20 molecules) from verified source ` to `data/raw/kinetic_dataset_raw.csv`. <!-- FAILED: unspecified -->
- [ ] T009e [P] [FR-009] Verify checksum (SHA-256) of `data/raw/kinetic_dataset_raw.csv` against the source manifest.
- [ ] T009f [P] [FR-009] Ingest verified data into `data/assets/kinetic_dataset.csv` with schema validation.
- [X] T009h [P] [FR-009/SC-006] **REMOVED**: Task to create reaction_type_lookup.csv removed per SC-006 requirement to validate against the entire dataset.
- [ ] T030 [P] [US3] **MOVED FROM PHASE 5**: Load curated reference set of known reactive substructures from `data/assets/reference_substructures.csv` (produced by T009c) to verify data availability for US3.
- [ ] T033 [P] [US3] **MOVED FROM PHASE 5**: Load the full `data/assets/kinetic_dataset.csv` (produced by T009f) AND the full `artifacts/model_comparison_results.json` (produced by T024); validate correlation between predicted gap and experimental rates for the **entire** dataset. **MUST** include a descriptive log entry analyzing reaction types where the proxy is theoretically strongest, without filtering the data. **Deliverable**: `artifacts/proxy_validation_report.json` containing `correlation_full_dataset`, `correlation_by_reaction_type_descriptive`, and `mechanistic_consistency_notes`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Feasible Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download QM9 subset and preprocess into graph structures using only CPU resources, ensuring memory safety.

**Independent Test**: The pipeline can be fully tested by executing the data download and preprocessing script on a CPU-only runner and verifying that the output graph objects are correctly formed and fit within memory limits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for SMILES parsing and exclusion logic in `tests/unit/test_parsing.py`
- [X] T011 [P] [US1] Integration test for full download → preprocess flow in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/01_download_data.py` to fetch QM9 subset (via `datasets.load_dataset('qm9', split='train')`) with error handling and retry logic
- [X] T013 [US1] Implement the preprocessing script in `code/02_preprocess_graphs.py` to convert SMILES to graphs using RDKit. **Includes**: <!-- FAILED: unspecified -->
 1. Memory profiling hook (using `psutil`) to detect usage > 4GB.
 2. **Automatic Trigger Logic**: If memory > 4GB, reduce batch size by [deferred] and re-attempt; if still failing, skip current molecule batch.
 3. Murcko scaffold splitting.
 4. Serialization to `.parquet`.
 5. **Artifact**: Generate `artifacts/memory_adjustment.log` documenting any sampling triggers and the specific actions taken (e.g., "Batch size reduced from 64 to 32").
 **Deliverable**: Output `.parquet` files in `data/processed/` with node features (atomic number, hybridization, formal charge) and edge features (bond type, conjugation).
- [X] T015 [US1] Implement Murcko scaffold splitting logic (standard train-test split) in `code/02_preprocess_graphs.py` (Integrated with T013)
- [ ] T016 [US1] Serialize preprocessed graphs to `data/processed/` (`.parquet` with compression `snappy`, filename pattern `qm9_processed_{split}.parquet`) with derivation logs and schema validation.
- [ ] T017 [US1] Add validation to ensure excluded invalid SMILES count is < 0.1% and **generate structured artifact** `artifacts/exclusion_report.json` containing `total_molecules`, `excluded_count`, `exclusion_percentage`, and `timestamp`. **Verification**: Confirm `artifacts/memory_adjustment.log` exists if sampling was triggered.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train lightweight Spectral GNN, Heterophily-aware GNN, and Random Forest baseline; compare performance.

**Independent Test**: The training and evaluation loop can be tested independently by running the training script for a fixed number of epochs and verifying that both models converge and produce metric logs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for model architecture initialization (CPU mode) in `tests/unit/test_models.py`
- [ ] T019 [P] [US2] Integration test for training loop convergence in `tests/integration/test_training.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement lightweight Spectral GNN architecture in `code/models/spectral_gnn.py` (CPU-only, no CUDA)
- [ ] T021 [US2] Implement Heterophily-aware GNN architecture in `code/models/hetero_gnn.py` (based on VR-GNN principles, CPU-only)
- [ ] T022 [US2] Implement Random Forest baseline using Morgan fingerprints in `code/models/random_forest_baseline.py`
- [ ] T023 [US2] Implement `code/train_models.py` to train all three models for a sufficient number of epochs (with early stopping: patience=5, metric='val_loss', target loss threshold=0.01) targeting the prediction of DFT-derived properties.
- [ ] T024 [US2] Implement `code/04_evaluate.py` to generate predictions and compute MSE, MAE, Pearson R for all models. **Deliverable**: Output `artifacts/model_comparison_results.json` with schema `{model: {mse, mae, pearson_r, predictions}, statistical_tests: {primary_test: 'wilcoxon', sensitivity_test: 't-test', p_value_wilcoxon, p_value_ttest}}`. **Note**: This task must explicitly tag the Wilcoxon signed-rank test as PRIMARY and the paired t-test as SENSITIVITY in the output JSON.
- [ ] T025 [US2] [US2] **Integration Test**: Write `tests/integration/test_statistics.py` to verify that `code/utils/metrics.py` (T006) correctly implements the Wilcoxon signed-rank test (PRIMARY) and paired t-test (SENSITIVITY) using mock data with known outcomes.
- [ ] T026 [US2] Log all model weights and metrics to `artifacts/` and `artifacts/metrics.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Attribution and Interpretability Analysis (Priority: P3)

**Goal**: Identify structural/electronic features contributing to predictions and validate against curated references.

**Independent Test**: The attribution analysis can be tested by running the GNNExplainer on a subset of molecules and verifying valid importance scores against the curated reference set.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for attribution score calculation in `tests/unit/test_attribution.py`
- [ ] T028 [P] [US3] Contract test for attribution output schema in `tests/contract/test_attribution_schema.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/05_attribution.py` using GNNExplainer or gradient-based methods to generate importance scores
- [ ] T030 [US3] **MOVED TO PHASE 2**: Load curated reference set of known reactive substructures from `data/assets/reference_substructures.csv` (produced by T009c).
- [ ] T031 [US3] Implement logic to aggregate importance scores across the dataset and rank the most significant structural/electronic features.
- [ ] T031b [US3] [US3] **Calculate Alignment**: Compute the alignment score between the top attributed substructures (from T031) and the curated reference set (from T030). **Deliverable**: Write `artifacts/alignment_score.json` containing the score.
- [ ] T031c [US3] [US3] **Verify Alignment**: Write `tests/contract/test_alignment_threshold.py` to assert that the score in `artifacts/alignment_score.json` is >= 0.7 (SC-003).
- [ ] T032a [US3] **REMOVED**: Task to filter kinetic dataset removed per SC-006 requirement to validate against the entire dataset.
- [ ] T033 [US3] **MOVED TO PHASE 2**: Load the full `data/assets/kinetic_dataset.csv` (produced by T009f) AND the full `artifacts/model_comparison_results.json` (produced by T024); validate correlation between predicted gap and experimental rates for the **entire** dataset. **MUST** include a descriptive log entry analyzing reaction types where the proxy is theoretically strongest, without filtering the data. **Deliverable**: `artifacts/proxy_validation_report.json`.
- [ ] T034 [US3] Generate attribution maps and validation reports in `artifacts/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` (include `quickstart.md` with run instructions)
- [ ] T036 Code cleanup and refactoring to ensure type hints and docstrings are complete
- [ ] T037 Performance optimization: Verify end-to-end runtime ≤ 6 hours and memory ≤ 4 GB on CI
- [ ] T038 [P] Additional unit tests for edge cases (invalid SMILES, download failures) in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation to ensure all artifacts are reproducible
- [ ] T040 Verify `state/` YAML is updated with SHA-256 hashes of final artifacts

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
- **User Story 2 (P2)**: Depends on US1 (requires preprocessed data)
- **User Story 3 (P3)**: Depends on US2 (requires trained models)

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

### Specific Task Dependencies (Critical for Execution)

- **T013** (Preprocessing + Memory Hooks) MUST complete before **T015** (Splitting) and **T016** (Serialization).
- **T017** (Exclusion Report) MUST complete after **T013** (Preprocessing) and **T016** (Serialization).
- **T009a** (Download Ref) MUST complete before **T009b** (Verify) and **T009c** (Ingest).
- **T009d** (Download Kinetic) MUST complete before **T009e** (Verify) and **T009f** (Ingest).
- **T030** (Load Ref) and **T033** (Validate Correlation) are now in Phase 2, ensuring they are available before US3 starts.
- **T033** (Validate Correlation) MUST complete after **T024** (Generate Predictions).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for SMILES parsing and exclusion logic in tests/unit/test_parsing.py"
Task: "Integration test for full download → preprocess flow in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/01_download_data.py to fetch QM9 subset..."
Task: "Implement code/02_preprocess_graphs.py to convert SMILES to graphs..."
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
 - Developer B: User Story 2 (waiting for data)
 - Developer C: User Story 3 (waiting for models)
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