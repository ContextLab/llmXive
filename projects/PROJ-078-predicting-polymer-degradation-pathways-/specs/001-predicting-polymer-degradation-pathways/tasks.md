# Tasks: Predicting Polymer Degradation Pathways with Graph Neural Networks

**Input**: Design documents from `/specs/001-polymer-degradation/`
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

- [ ] T001a Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `data/reports/`, `tests/`, `state/`
- [ ] T001b Set permissions and initialize git repository
- [X] T002 Initialize Python 3.11 project by generating `code/requirements.txt` with pinned versions: `rdkit`, `torch`, `torch-geometric`, `scikit-learn`, `pandas`, `numpy`, `pyyaml`, `requests`, `statsmodels`
- [X] T003 [P] Configure linting (`ruff` or `flake8`) and formatting (`black`) tools in `code/.ruff.toml` or `code/.flake8`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup shared logging infrastructure with file handlers in `code/utils.py`
- [X] T005 Implement exponential backoff utility (max limited retries) in `code/utils.py` for API rate limiting
- [X] T006 Create base configuration loader for environment variables and paths in `code/utils.py`
- [X] T007 Define `PolymerRecord` and `MolecularGraph` data classes in `code/data_models.py`
- [ ] T008 Setup pytest framework and directory structure (`tests/unit`, `tests/integration`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, filter, and convert polymer degradation records from NIST Chemistry WebBook and Materials Project into a structured graph dataset.

**Independent Test**: Can be fully tested by executing the ingestion script against a small subset of known NIST entries and verifying the output CSV contains valid SMILES strings, numeric environmental parameters, and categorical degradation labels.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [US1] Unit test for SMILES validation and RDKit graph conversion in `tests/unit/test_ingest.py::test_smiles_validation_rejects_invalid`
- [X] T010 [US1] Unit test for missing data exclusion logic in `tests/unit/test_preprocess.py::test_missing_env_excludes_record`
- [X] T012 [US1] Integration test for API rate-limit backoff in `tests/integration/test_api_ingestion.py::test_backoff_on_rate_limit`

### Implementation for User Story 1

- [ ] T013 [US1] (Depends on T007) Implement `ingest.py`: Download records from NIST/Materials Project with rate-limit backoff (FR-001, FR-008)
- [X] T014 [US1] (Depends on T007) Implement `ingest.py`: Identify records missing 'degradation pathway' labels; FLAG them by saving to `data/raw/flagged_for_curation.csv` and log the action. EXCLUDE these specific records from the immediate training set to prevent label leakage, preserving the 'flag' as a distinct artifact for potential manual curation (FR-008, US-1 Scenario 2)
- [ ] T015 [US1] (Depends on T007) Implement `preprocess.py`: Convert SMILES to molecular graphs using RDKit; handle valid records (FR-002)
- [X] T015b [US1] (Depends on T015) Implement `preprocess.py`: FLAG records with missing environmental data (temp/pH/UV) by saving their IDs to `data/raw/flagged_env_data.csv` and logging the action. **DEFAULT PATH**: EXCLUDE these records from the training set to prevent confounding. (FR-002, US-1 Scenario 2, Plan: Data Exclusion Assumption)
- [X] T015c [US1] (Depends on T015) **IMPUTATION PATH DOCUMENTATION**: Explicitly document the rejection of the imputation path defined in FR-002. Generate `data/reports/imputation_decision_log.json` specifying the default values (pH 7, 25°C, No UV) that *would* have been used, and the scientific rationale for exclusion (confounding). (FR-002 Traceability)
- [X] T016a [US1] (Depends on T014) Implement `ingest.py`: Save the raw ingested dataset (after label flagging) to `data/raw/raw_polymer_records.csv` with checksums. (FR-001)
- [X] T016b [US1] (Depends on T016a, T015) Implement `preprocess.py`: Save the processed graph dataset (after SMILES conversion and environmental filtering) to `data/processed/processed_graph_dataset.csv` with checksums. (FR-002)
- [X] T016c [US1] (Depends on T016b) **PRE-AUGMENTATION SAVE**: Save the pre-augmentation dataset (after environmental filtering but before augmentation) to `data/processed/pre_augmented_graph_dataset.csv` with checksums. This artifact is the input for the augmentation phase in Phase 4. (FR-002)
- [ ] T017 [US1] (Depends on T016b) Perform statistical power analysis on the filtered dataset: Read `data/processed/processed_graph_dataset.csv`. **Logic**:
 - If n > 150: Trigger T018 (Subsampling).
 - If 50 <= n <= 150: Write `state/augmentation_trigger.json` with `{"n": <int>, "action": "augment"}`. This triggers T025 in Phase 4.
 - If n < 50: Write `state/augmentation_trigger.json` with `{"n": <int>, "action": "augment_aggressive"}` AND generate `data/reports/power_analysis_report.json` with keys `{"n": <int>, "power_warning": true, "action": "augment_aggressive"}`. The pipeline PROCEEDS with augmentation; `power_warning` is a metadata flag only. (SC-004, Constitution VII)
- [ ] T018 [US1] (Depends on T017) **SUBSAMPLING LOGIC**: If n > 150 or n < 50, implement `preprocess.py` to subsample the dataset to a representative subset of instances (or all if n < 50) using a fixed random seed (e.g., a predetermined value) and **stratified sampling** by degradation pathway. Save the subsampled dataset to `data/processed/subsampled_polyesters.csv` and log the action (Plan: Small Dataset Robustness, Constitution I).
- [ ] T019 [US1] (Depends on T016b, T018) **DATA SAVING**: Implement `preprocess.py`: Save the final processed dataset.
 - If T017 triggered augmentation (n <= 150): Skip saving here (T016c is the pre-augmented source).
 - If T017 triggered subsampling (n > 150 or n < 50): Save the subsampled set to `data/processed/subsampled_polyesters.csv` (already done in T018).
 - Note: This task is now primarily for logging. The actual final dataset is produced by T019b. (FR-002, FR-004)
- [ ] T019b [US1] (Depends on T016d OR T018) **FINAL DATASET CONSOLIDATION**: Ensure `data/processed/final_dataset.csv` exists.
 - If augmentation was triggered (T025 ran): Copy `data/processed/augmented_graph_dataset.csv` to `data/processed/final_dataset.csv`.
 - If subsampling was triggered (T018 ran): Copy `data/processed/subsampled_polyesters.csv` to `data/processed/final_dataset.csv`.
 - Log the source of the final dataset. (Unified Artifact Path)
- [X] T020 [US1] (Depends on T007) Add logging for data ingestion actions, exclusions, flags, and power analysis warnings in `code/ingest.py` and `code/preprocess.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight GNN Training and Feature Attribution (Priority: P2)

**Goal**: Train a lightweight Graph Neural Network (≤3 layers, hidden dim ≤128) on the prepared dataset and generate feature importance scores via Integrated Gradients.

**Independent Test**: Can be fully tested by running the training script on a fixed random seed, verifying the model converges within 6 hours on a CPU-only runner, and confirming that the Integrated Gradients output highlights specific atoms/bonds in the polymer chain.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [US2] Unit test for GNN architecture constraints (layers ≤3, dim ≤128) in `tests/unit/test_model.py::test_gnn_layers_constraint`
- [X] T022 [US2] Unit test for Integrated Gradients calculation on a dummy graph in `tests/unit/test_model.py::test_integrated_gradients_on_dummy_graph`
- [X] T023 [US2] Integration test for training loop convergence on CPU in `tests/integration/test_training.py::test_training_converges_cpu`

### Implementation for User Story 2

- [ ] T024 [US2] (Depends on T019b) Implement `model.py`: Define lightweight GNN architecture (≤3 layers, hidden dim ≤128) CPU-only (FR-003)
- [ ] T025 [US2] (Depends on T016c, `state/augmentation_trigger.json`) **AUGMENTATION PATH (Plan Correction)**: Check for `state/augmentation_trigger.json`. If present (50 <= n <= 150 or n < 50):
 - Apply data augmentation via **functional-group-preserving edge dropout** (non-ester bonds only) and SMILES canonicalization.
 - **Algorithm**: Use RDKit to identify ester bonds (C(=O)O pattern) and mask only non-ester bonds with a a moderate dropout rate.
 - **Constraint**: DO NOT implement bond rotation or atom masking. Assert that no bond rotation logic is present.
 - Log chemical validity checks.
 - Save the augmented dataset to `data/processed/augmented_graph_dataset.csv` with checksums.
 - If trigger file is absent (n > 150), log status="skipped" in `data/processed/augmentation_log.json`. (FR-004, Plan Correction)
- [ ] T025b [US2] (Depends on T025) **AUGMENTATION TIMING**: Measure the runtime of the augmentation step. Log the duration to `data/reports/augmentation_timing.json`. **Constraint**: If duration > 30 minutes, log a FAIL status; otherwise PASS. (US-2 Scenario 3, FR-004)
- [ ] T025c [US2] (Depends on T025) **AUGMENTATION DOCUMENTATION**: Generate `data/reports/augmentation_methodology.json` explicitly documenting the rejection of FR-004's "bond rotation and atom masking" requirement, citing the Plan's correction for chemical validity, and confirming the implementation of "functional-group-preserving edge dropout". (FR-004 Traceability)
- [ ] T016d [US2] (Depends on T025) **POST-AUGMENTATION SAVE**: Save the final augmented dataset (result of T025) to `data/processed/augmented_graph_dataset.csv` with checksums. This artifact is the input for the training phase. (FR-004)
- [ ] T028 [US2] (Depends on T019b) Implement `train.py`: Training loop with k-fold cross-validation (or leave-one-out if n < 50) and random seed pinning. Report mean macro-F1 and convergence check (loss within 5% over last 5 epochs). (FR-003, US-2 Scenario 1)
- [ ] T029 [US2] (Depends on T028) Implement `model.py`: Compute feature importance scores using Integrated Gradients on the trained model. (FR-005)
- [ ] T030 [US2] (Depends on T029) Implement `evaluate.py`: Calculate percentage of hydrolysis cases where ester bonds are in top `THRESHOLD_TOP_PERCENT` (default a predetermined threshold, loaded from `code/config.yaml`) of attribution scores. **Validation**: Compare this percentage against the established threshold.. Generate `data/reports/ester_attribution_check.json` with keys `{"percentage": float, "threshold": a high confidence level, "status": "PASS|FAIL"}`. (SC-005)
- [ ] T031 [US2] (Depends on T030) Implement `evaluate.py`: Save model checkpoints, validation metrics (macro-F1), and IG attribution maps to `data/reports/`. (FR-003, FR-005)
- [ ] T032 [US2] (Depends on T031) Implement `evaluate.py`: Generate test-set predictions using the trained model; save predictions to `data/reports/test_predictions.json` for downstream validation. (FR-007)
- [ ] T033 [US2] (Depends on T019b) Add logging for training progress, validation scores, augmentation stats, and runtime constraints in `code/train.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Motif Reporting (Priority: P3)

**Goal**: Receive a statistical report confirming that the identified structure-mechanism correlations are significant (via permutation test) and listing a limited set of the most prominent structural motifs.

**Independent Test**: Can be fully tested by running the analysis script on the final model outputs and verifying the generated report contains a p-value from the permutation test and a ranked list of motifs.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [US3] Unit test for permutation test logic (shuffling motifs) in `tests/unit/test_evaluate.py::test_permutation_test_shuffling`
- [ ] T035 [US3] Unit test for motif extraction and ranking logic in `tests/unit/test_evaluate.py::test_motif_extraction_ranking`
- [ ] T036 [US3] Integration test for full report generation pipeline in `tests/integration/test_reporting.py::test_full_report_generation`

### Implementation for User Story 3

- [ ] T037 [US3] (Depends on T031, T019b) **SCIENTIFIC VALIDATION (Permutation)**: Implement `evaluate.py`: Perform Permutation Test by **shuffling input motifs** (as per FR-006) using 'Motif-Masking' as the specific mechanism.
 - **Statistic Definition**: `observed_stat` = mean macro-F1 score drop between original model and motif-masked model.
 - **Null Distribution**: Generate a sufficient number of permutations to ensure statistical robustness..
 - **Mapping**: Explicitly document that 'Motif-Masking' implements the 'shuffling input motifs' requirement from US-3 Scenario 1.
 - Generate `data/reports/permutation_test_results.json` with schema: `{'bins': [float], 'counts': [int], 'observed_stat': float, 'p_value': float}` (FR-006, SC-002, US-3 Scenario 1)
- [ ] T038 [US3] (Depends on T031) **CONSTITUTIONAL VALIDATION (χ²)**: Implement `evaluate.py`: Implement χ² Discretization Protocol.
 - **Binning**: Apply 'quantile-based binning' (top quantile vs rest) on absolute Integrated Gradients scores.
 - **Tie-Breaking**: If a score is at a low percentile threshold, assign it to the 'Low' bin.
 - **Validation**: Log bin counts and verify distribution is uniform before proceeding.
 - Generate `data/reports/chisquare_validation.csv` with schema: columns `['bin_id', 'observed_count', 'expected_count', 'chi_sq_contrib']` and a summary row `['TOTAL',...,..., 'chi_sq_stat']`. (Constitution VI, Plan Complexity Tracking)
- [ ] T039 [US3] (Depends on T031) Implement `evaluate.py`: Aggregate feature importances to identify a small set of top structural motifs and their correlation with degradation types. (FR-007)
- [ ] T040 [US3] (Depends on T031) Implement `evaluate.py`: Generate final report in `data/reports/` including p-values, motif list, and confidence flags (FR-007)
- [ ] T041 [US3] (Depends on T031) Implement `evaluate.py`: Add logic to flag predictions with confidence < `CONFIDENCE_THRESHOLD` (configurable, default a moderate threshold) as "low confidence" in the report (US-3 Acceptance Scenario 3, Plan: Data Exclusion)
- [ ] T042 [US3] (Depends on T031) Add logging for statistical test results and report generation in `code/evaluate.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Generate `README.md` in repository root with usage examples, setup instructions, and data schema sections
- [ ] T044 [P] Generate `docs/usage.md` with detailed API and script documentation
- [ ] T045 [P] Refactor `code/utils.py` to ensure shared utilities are modular and tested
- [ ] T046 [P] Refactor `code/data_models.py` to ensure data classes are robust and validated
- [ ] T047 [P] Implement memory monitoring utility in `code/utils.py`
- [ ] T048 [P] Integrate subsampling trigger in `code/preprocess.py` if memory > 7GB
- [ ] T049 [P] Additional unit tests for edge cases in `tests/unit/`: `test_invalid_smiles_raises`, `test_empty_dataset_raises`
- [ ] T050 [P] Run `quickstart.md` validation to ensure end-to-end pipeline executes within 6 hours

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1 (T019b)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model outputs from US2 (T031)

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
Task: "Unit test for SMILES validation and RDKit graph conversion in tests/unit/test_ingest.py::test_smiles_validation_rejects_invalid"
Task: "Unit test for missing data exclusion logic in tests/unit/test_preprocess.py::test_missing_env_excludes_record"

# Launch implementation tasks for User Story 1 together (if dependencies allow):
Task: "Implement ingest.py: Download records..."
Task: "Implement preprocess.py: Convert SMILES to molecular graphs..."
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model Training) - *Wait for T019b output*
 - Developer C: User Story 3 (Validation) - *Wait for T031 output*
3. Stories complete and integrate independently

---

## Methodological Corrections

**⚠️ MANDATORY INSTRUCTIONS FOR IMPLEMENTERS**

The following rules override any conflicting instructions in `spec.md` or previous drafts. These are the **only** valid instructions for this project:

1. **Data Handling Distinction**:
 - **Missing Labels**: Records missing 'degradation pathway' labels MUST be **FLAGGED** (saved to `data/raw/flagged_for_curation.csv`) for manual review, then excluded from the immediate training set. This satisfies FR-008 and US-1 Scenario 2.
 - **Missing Environmental Data (Default Path)**: Records missing environmental data (temp/pH/UV) MUST be **FLAGGED** (saved to `data/raw/flagged_env_data.csv`) and **EXCLUDED** from the training set to prevent confounding. This is the DEFAULT and ONLY scientific approach.
 - **NO IMPUTATION PATH EXISTS**: The Spec's requirement for imputation (FR-002) is methodologically flawed and rejected by the Plan. Do NOT implement any imputation logic. (Documented in T015c).
2. **Augmentation Strategy**:
 - **T025 (Plan Correction)**: Implement 'functional-group-preserving edge dropout' (non-ester bonds only) and SMILES canonicalization. Skip if n > 150.
 - **Bond Rotation Removal**: The Spec's requirement for 'bond rotation and atom masking' is chemically invalid. Do NOT implement this method. (Documented in T025c).
 - **Verification**: T025 MUST include a step to verify that NO bond rotation logic was applied.
3. **Statistical Validation**:
 - **T038 (Constitutional)**: Implement χ² Discretization Protocol to satisfy Constitution Principle VI. This is the PRIMARY validation method required by the Constitution.
 - **T037 (Scientific)**: Implement 'shuffling input motifs' (as per FR-006) using 'Motif-Masking' as the specific mechanism. This is the complementary scientific validation.
4. **Thresholds**: For SC-004, trigger a warning if n < 150. For SC-005, use a configurable variable `THRESHOLD_TOP_PERCENT` (default 10) for verification. For US-3, use `CONFIDENCE_THRESHOLD` (default 0.6).

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All data ingestion must use real URLs; no synthetic data generation allowed.
- **CRITICAL**: Records with missing environmental data (temp/pH/UV) MUST be FLAGGED then EXCLUDED (ONLY PATH).
- **CRITICAL**: Records with missing labels MUST be FLAGGED for curation before exclusion (FR-008).
- **CRITICAL**: GNN must run on CPU only; no CUDA/GPU dependencies.
- **CRITICAL**: Only Edge Dropout (T025) is implemented. Bond Rotation is REMOVED.
- **CRITICAL**: χ² Test (T038) is Constitutional/Primary; Permutation Test (T037) is Scientific/Complementary.
- **CRITICAL**: Confidence threshold < `CONFIDENCE_THRESHOLD` (configurable, default 0.6) is MANDATORY for flagging low-confidence predictions (US-3 Scenario 3, Plan).