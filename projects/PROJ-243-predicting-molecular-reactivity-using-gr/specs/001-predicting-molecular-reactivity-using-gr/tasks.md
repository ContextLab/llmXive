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

- [ ] T001a [P] Create data directory: `data/raw`
- [ ] T001b [P] Create data directory: `data/processed`
- [ ] T001c [P] Create data directory: `data/assets`
- [ ] T002 [P] Create code and artifact directories: `code`, `artifacts`, `tests`
- [X] T003 [P] Initialize Python 3.11 project with `requirements.txt` (pinning `torch`, `rdkit`, `scikit-learn`, `pandas`, `datasets`, `networkx`, `psutil`)
- [ ] T004 [P] Configure linting (flake8/ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `code/data/download.py` with robust retry logic (exponential backoff) for dataset downloads; **MUST** implement orchestration logic to exit with a clear error code and log the specific failure reason after retries are exhausted, as required by spec Edge Cases.
- [X] T006 [P] Implement `code/utils/graph_utils.py` for molecular graph construction (SMILES → Node/Edge features)
- [X] T007 [P] Implement `code/utils/metrics.py` for MSE, MAE, Pearson R, **Wilcoxon signed-rank test (PRIMARY per Plan.md)**, and **paired t-test (SENSITIVITY per Plan.md)**. **CRITICAL**: This utility must be the single source of truth for statistical tests; T025 will test this utility.
- [X] T008 [P] Create base configuration management (`code/config.py`) for random seeds and device settings (`device='cpu'`)
- [ ] T009 [P] Setup logging infrastructure to write structured logs to `artifacts/logs/` and `artifacts/metrics.json`
- [X] T010g [P] [FR-008/FR-009] Create `data/raw/checksums_schema.json` defining the **expected** SHA-256 hashes for:
 - `reference_substructures`: The curated static file (to be generated/verified).
 - `kinetic_dataset`: The local static asset file (to be verified).
 - **MUST** include the source URL and version for the kinetic dataset to ensure reproducibility.
- [ ] T010h [P] [FR-008/FR-009] **POPULATE CHECKSUMS**: After T010a and T010d complete, compute SHA-256 hashes of `data/raw/reference_substructures_raw.csv` and `data/raw/kinetic_dataset_raw.csv` and update `data/raw/checksums.json` with the actual hashes. <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->
- [ ] T010a [P] [FR-008] **FETCH REFERENCE SET**: Fetch the curated reference set of known reactive substructures from NIST (Public Literature). using `code/data/download.py` with URL ` (or specific NIST dataset ID for reactive substructures). **MUST** save as `data/raw/reference_substructures_raw.csv`. **NO** synthetic generation. <!-- FAILED: unspecified -->
- [ ] T010b [P] [FR-008] Verify checksum (SHA-256) of `data/raw/reference_substructures_raw.csv` against the hash in `data/raw/checksums.json`. <!-- FAILED: unspecified -->
- [X] T010c [P] [FR-008] Ingest verified data into `data/assets/reference_substructures.csv` with schema validation.
- [ ] T010d [P] [FR-009] **FETCH KINETIC DATASET**: Fetch the external kinetic dataset of ≥20 molecules with experimental reaction rates from PubChem (Public Literature) using `code/data/download.py` with URL ` (or specific PubChem dataset ID). **MUST** save as `data/raw/kinetic_dataset_raw.csv`. **NO** static asset assumption.
- [ ] T010e [P] [FR-009] Verify checksum (SHA-256) of `data/raw/kinetic_dataset_raw.csv` against the hash in `data/raw/checksums.json`. <!-- FAILED: unspecified -->
- [X] T010f [P] [FR-009] Ingest verified external kinetic data into `data/assets/kinetic_dataset.csv` with schema validation.
- [X] T010h [P] [FR-009/SC-006] **VALIDATE DATA AVAILABILITY**: Ensure `data/assets/kinetic_dataset.csv` and `data/assets/reference_substructures.csv` exist before proceeding to Phase 3.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Feasible Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download QM9 subset and preprocess into graph structures using only CPU resources, ensuring memory safety.

**Independent Test**: The pipeline can be fully tested by executing the data download and preprocessing script on a CPU-only runner and verifying that the output graph objects are correctly formed and fit within memory limits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T011 [P] [US1] Unit test for SMILES parsing and exclusion logic in `tests/unit/test_parsing.py`
- [X] T012 [P] [US1] Integration test for full download → preprocess flow in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/01_download_data.py` to fetch QM9 subset (via `datasets.load_dataset('qm9', split='train')`) with error handling and retry logic
- [X] T014a [US1] **Estimate & Sample**: Implement `code/02_preprocess_graphs.py` logic to estimate total memory required for the full dataset. If estimated > 4GB, **sample N molecules** (using a fixed seed) to fit within 4GB *before* graph construction begins. Log the sampling strategy and N to `artifacts/memory_adjustment.log`.
- [X] T014b [US1] **Preprocess Graphs**: Implement the core preprocessing logic in `code/02_preprocess_graphs.py` to convert SMILES to graphs using RDKit. **Includes**:
 1. **Memory Safety Logic**: During batch processing, if memory usage exceeds 4GB, reduce batch size by half (integer division) with a hard floor at a minimum viable threshold, then re-attempt. Log the specific adjustment in `artifacts/memory_adjustment.log`.
 2. Invalid SMILES handling: Log and exclude molecules; target < 0.1% exclusion.
 3. **Deliverable**: Intermediate graph objects serialized to `data/processed/qm9_graphs_intermediate.parquet`.
- [ ] T014c [US1] **Generate Exclusion Report & Validate**: Implement logic to validate excluded invalid SMILES count is < 0.1% and **generate structured artifact** `artifacts/exclusion_report.json` containing `total_molecules`, `excluded_count`, `exclusion_percentage`, and `timestamp`. **Verification**: Confirm `artifacts/memory_adjustment.log` exists if sampling was triggered. **MUST** explicitly log 'N molecules sampled', 'seed value', and 'original count' to `artifacts/memory_adjustment.log` if sampling occurred.
- [ ] T016 [US1] [US1] **Serialization**: Serialize preprocessed graphs to `data/processed/` (`.parquet` with compression `snappy`, filename pattern `qm9_processed_{split}.parquet` where `{split}` is explicitly 'train' or 'test') with derivation logs and schema validation. **Includes** Murcko scaffold splitting. **Deliverable**: `data/processed/qm9_processed_train.parquet` and `data/processed/qm9_processed_test.parquet`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train lightweight Spectral GNN, Heterophily-aware GNN, and Random Forest baseline; compare performance.

**Independent Test**: The training and evaluation loop can be tested independently by running the training script for a fixed number of epochs and verifying that both models converge and produce metric logs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for model architecture initialization (CPU mode) in `tests/unit/test_models.py`
- [ ] T018 [P] [US2] Integration test for training loop convergence in `tests/integration/test_training.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement lightweight Spectral GNN architecture in `code/models/spectral_gnn.py` (CPU-only, no CUDA)
- [ ] T020 [US2] Implement Heterophily-aware GNN architecture in `code/models/hetero_gnn.py` (based on VR-GNN principles, CPU-only)
- [ ] T021 [US2] Implement Random Forest baseline using Morgan fingerprints in `code/models/random_forest_baseline.py`
- [ ] T022 [US2] Implement `code/train_models.py` to train all three models for a sufficient number of epochs (with early stopping: patience=5, metric='val_loss') targeting the prediction of DFT-derived properties. **Note**: Convergence criteria defined in `code/config.py`, not hardcoded.
- [ ] T023a [US2] **Generate Predictions**: Implement `code/04_evaluate.py` to generate predictions for all models. **Deliverable**: Output `artifacts/predictions.json` with model predictions.
- [ ] T023b [US2] **Compute Metrics**: Implement metric computation (MSE, MAE, Pearson R) in `code/04_evaluate.py`. **Deliverable**: Output `artifacts/metrics.json` with metrics for all models.
- [ ] T023c [US2] **Statistical Tests**: Implement statistical tests in `code/04_evaluate.py`. **Primary**: Wilcoxon signed-rank test (as per Plan.md Methodological Note). **Sensitivity**: Paired t-test (as per FR-006 sensitivity analysis). **CRITICAL**: Apply Bonferroni correction (alpha_adj = 0.05/3) and log corrected p-values. **Explicit Step**: Run paired t-test and record results in `model_comparison_results.json` to satisfy FR-006 sensitivity requirement. **Deliverable**: Write output to `artifacts/model_comparison_results.json` with schema `{model: {mse, mae, pearson_r, predictions}, statistical_tests: {primary_test: 'wilcoxon', sensitivity_test: 't-test', p_value_wilcoxon, p_value_ttest, alpha_adj:}}`.
- [ ] T023d [US2] **Document Statistical Justification**: Write `artifacts/statistical_justification.md` explicitly explaining why the **Wilcoxon signed-rank test** was chosen as the primary test over the **paired t-test** (mandated by FR-006 as sensitivity) due to heteroscedasticity and non-normality of residuals, as per the Methodological Note in plan.md. This task ensures compliance with FR-006 by documenting the deviation.
- [ ] T024 [US2] [US2] **Integration Test**: Write `tests/integration/test_statistics.py` to verify that `code/utils/metrics.py` (T007) correctly implements the Wilcoxon signed-rank test (PRIMARY) and paired t-test (SENSITIVITY) using mock data with known outcomes.
- [ ] T025 [US2] Log all model weights to `artifacts/model_weights.tar.gz` (compressed archive of `code/models/` weights) with checksums.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Attribution and Interpretability Analysis (Priority: P3)

**Goal**: Identify structural/electronic features contributing to predictions and validate against curated references.

**Independent Test**: The attribution analysis can be tested by running the GNNExplainer on a subset of molecules and verifying valid importance scores against the curated reference set.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for attribution score calculation in `tests/unit/test_attribution.py`
- [ ] T027 [P] [US3] Contract test for attribution output schema in `tests/contract/test_attribution_schema.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/05_attribution.py` using GNNExplainer or gradient-based methods to generate importance scores
- [ ] T029 [US3] Load curated reference set of known reactive substructures from `data/assets/reference_substructures.csv` (produced by T010c).
- [ ] T030 [US3] Implement logic to aggregate importance scores across the dataset and rank the most significant structural/electronic features.
- [ ] T030b [US3] [US3] **Calculate Alignment**: Compute the alignment score between the top attributed substructures (from T030) and the curated reference set (from T029). **Deliverable**: Write `artifacts/alignment_score.json` containing the score.
- [ ] T030c [US3] [US3] **Verify Alignment**: Write `tests/contract/test_alignment_threshold.py` to assert that the score in `artifacts/alignment_score.json` is >= 0.7 (SC-003).
- [ ] T031 [US3] Load the full `data/assets/kinetic_dataset.csv` (produced by T010f) AND the full `artifacts/model_comparison_results.json` (produced by T023c); validate correlation between predicted gap and experimental rates for the **entire** dataset. **MUST** include a descriptive log entry analyzing reaction types where the proxy is theoretically strongest, but restrict scientific interpretation to those specific reaction types. **Deliverable**: `artifacts/proxy_validation_report.json` containing `correlation_full_dataset`, `correlation_by_reaction_type_descriptive`, and `mechanistic_consistency_notes`. **ERROR HANDLING**: If `data/assets/kinetic_dataset.csv` is missing, log 'MISSING_DATA' and exit gracefully.
- [ ] T032 [US3] Generate attribution maps and validation reports in `artifacts/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `docs/` (include `quickstart.md` with run instructions)
- [ ] T034 Code cleanup and refactoring to ensure type hints and docstrings are complete
- [ ] T035 Performance optimization: Verify end-to-end runtime ≤ 6 hours and memory ≤ 4 GB on CI
- [ ] T036 [P] Additional unit tests for edge cases (invalid SMILES, download failures) in `tests/unit/`
- [ ] T037 Run `quickstart.md` validation to ensure all artifacts are reproducible
- [ ] T038 Verify `state/` YAML is updated with SHA-256 hashes of final artifacts
- [ ] T039 [P] Final review of all artifacts against Constitution principles

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

- **T014a** (Estimate/Sample) MUST complete before **T014b** (Preprocess).
- **T014b** (Preprocess) MUST complete before **T014c** (Exclusion Report).
- **T014c** (Exclusion Report) MUST complete before **T016** (Serialization).
- **T010g** (Create Checksums) MUST complete before **T010a** (Fetch Ref) and **T010d** (Fetch Kinetic).
- **T010a** (Fetch Ref) MUST complete before **T010b** (Verify) and **T010c** (Ingest).
- **T010d** (Fetch Kinetic) MUST complete before **T010e** (Verify) and **T010f** (Ingest).
- **T010h** (Populate Checksums) MUST complete after **T010a** and **T010d**.
- **T030** (Load Ref) and **T031** (Validate Correlation) are now in Phase 5, ensuring they are available after US2 completes.
- **T031** (Validate Correlation) MUST complete after **T023c** (Statistical Tests) and **T023d** (Justification).
- **T023a**, **T023b**, **T023c**, **T023d** are sequential within Phase 4.

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