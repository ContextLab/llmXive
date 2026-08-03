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
- [ ] T001b Set permissions and initialize git repository: Run `git init` in repository root. **Verification**: Verify `.git` directory exists and run `git status` to confirm clean state. Log output. (Constitution I)
- [X] T002 (Depends on T001b) Initialize Python 3.11 project by generating `code/requirements.txt` with pinned versions: `rdkit`, `torch`, `torch-geometric`, `scikit-learn`, `pandas`, `numpy`, `pyyaml`, `requests`, `statsmodels`
- [X] T003 [P] Configure linting (`ruff` or `flake8`) and formatting (`black`) tools in `code/.ruff.toml` or `code/.flake8`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 (Depends on T001b) Setup shared logging infrastructure with file handlers in `code/utils.py`
- [X] T005 (Depends on T001b) Implement exponential backoff utility (max limited retries) in `code/utils.py` for API rate limiting
- [X] T006 (Depends on T001b) Create base configuration loader for environment variables and paths in `code/utils.py`
- [X] T007 (Depends on T001b) Define `PolymerRecord` and `MolecularGraph` data classes in `code/data_models.py`
- [ ] T008 (Depends on T001b) Setup pytest framework and directory structure (`tests/unit`, `tests/integration`)

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

- [ ] T013 [US1] (Depends on T007) Implement `ingest.py`: Download records from NIST (URL: `https://webbook.nist.gov/cgi/cbook.cgi?ID=...`) and Materials Project (API Endpoint: `https://materialsproject.org/rest/v2/materials/...`) with rate-limit backoff. **Output**: Save to `data/raw/raw_nist_mp_records.csv` with schema: `[smiles, temperature, ph, uv, degradation_pathway, source_id]`. (FR-001, FR-008)
- [X] T014 [US1] (Depends on T007) Implement `ingest.py`: Identify records missing 'degradation pathway' labels; FLAG them by saving to `data/raw/flagged_for_curation.csv` and log the action. EXCLUDE these specific records from the immediate training set to prevent label leakage, preserving the 'flag' as a distinct artifact for potential manual curation (FR-008, US-1 Scenario 2)
- [ ] T015 [US1] (Depends on T007) Implement `preprocess.py`: Convert SMILES to molecular graphs using RDKit (parameters: `sanitize=True`, `removeHs=False`); filter non-polyesters by detecting ester functional groups (pattern: `C(=O)O`) in SMILES; encode environmental conditions (temp/pH/UV) as continuous node features; **Output**: Save to `data/processed/graphs.parquet` (FR-002)
- [X] T015b [US1] (Depends on T015) Implement `preprocess.py`: FLAG records with missing environmental data (temp/pH/UV) by saving their IDs to `data/raw/flagged_env_data.csv` and logging the action. **DEFAULT PATH**: EXCLUDE these records from the training set to prevent confounding. (FR-002, US-1 Scenario 2, Plan: Data Exclusion Assumption)
- [X] T015c [US1] (Depends on T015) **IMPUTATION REJECTION DOCUMENTATION**: Generate `data/reports/imputation_decision_log.json` explicitly documenting the rejection of the imputation path defined in FR-002. **Schema**: `{"rationale": "string", "default_values": {"pH": 7, "temp": 25, "uv": 0 (Wikipedia: Wavefront .obj file, https://en.wikipedia.org/wiki/Wavefront_.obj_file)}, "exclusion_count": int, "exclusion_reason": "confounding"}`. (FR-002 Traceability)
- [X] T016a [US1] (Depends on T014) Implement `ingest.py`: Save the raw ingested dataset (after label flagging) to `data/raw/raw_polymer_records.csv` with checksums. (FR-001)
- [X] T016b [US1] (Depends on T015) Implement `preprocess.py`: Save the processed graph dataset (after SMILES conversion, polyester filtering, and environmental filtering) to `data/processed/processed_graph_dataset.csv` with checksums. (FR-002)
- [X] T016c [US1] (Depends on T016b) **PRE-AUGMENTATION SAVE**: Save the pre-augmentation dataset (after environmental filtering but before augmentation) to `data/processed/pre_augmented_graph_dataset.csv` with checksums. This artifact is the input for the augmentation phase in Phase 4. (FR-002)
- [ ] T017a [US1] (Depends on T016b) **POWER ANALYSIS**: Perform statistical power analysis on the filtered dataset: Read `data/processed/processed_graph_dataset.csv`. **Logic**:
 - Library: `statsmodels.stats.power`
 - Calculate sample size `n`.
 - **Output**: Write `data/reports/power_analysis_report.json` with `{"n": int}`.
 - **Trigger**: If n < 150, generate a warning flag in the report. (SC-004)
- [ ] T017b [US1] (Depends on T017a) **SUBSAMPLING PATH**: If `n > 150`:
 - Implement `preprocess.py` to subsample the dataset to a representative subset of instances using a fixed random seed `42` and **stratified sampling** by the `degradation_pathway` column.
 - **Output**: Save the subsampled dataset directly to `data/processed/final_dataset.csv` with checksums.
 - Log the action and the sampling ratio.
 - Write `state/augmentation_trigger.json` with `{"n": int, "action": "none"}`. (FR-002, FR-004, Plan: Small Dataset Robustness)
- [ ] T017c [US1] (Depends on T017a) **AUGMENTATION TRIGGER PATH**: If `n <= 150`:
 - Write `state/augmentation_trigger.json` with `{"n": int, "action": "augment"}` (if 50<=n<=150) or `{"n": int, "action": "augment_aggressive"}` (if n<50).
 - Generate `data/reports/power_analysis_warning.txt` with a human-readable warning. This triggers T025a in Phase 4.
 - **Note**: This task implements the Plan Correction for SC-004, explicitly referencing the Plan's amendment for n<50 aggressive augmentation. (SC-004, Constitution VII, Plan Correction)
- [X] T019 [US1] (Depends on T017b OR T017c) **DATA INTEGRITY CHECK**: Verify the checksums of `data/processed/processed_graph_dataset.csv` and `data/processed/final_dataset.csv` (if created). Log any discrepancies. (Plan: Data Hygiene)
- [X] T019b [US1] (Depends on T017b OR T017c) **METADATA GENERATION**: Generate `data/processed/dataset_metadata.json` containing the count of records, count of excluded records, and the action taken (none/augment/augment_aggressive). (Plan: Data Hygiene)
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

- [ ] T024 [US2] (Depends on T017b OR T017c) Implement `model.py`: Define lightweight GNN architecture (GCN variant, ≤3 layers, hidden dim ≤128, activation=ReLU, pooling=mean) CPU-only. **Input Shape**: `[num_nodes, num_features]`, **Output Shape**: `[num_nodes, num_classes]`. (FR-003)
- [ ] T025a [US2] (Depends on T017c) **AUGMENTATION TRIGGER DECISION**: Read `state/augmentation_trigger.json`.
 - If `action` is "none" (from T017b), log status="skipped" in `data/processed/augmentation_log.json` and skip to T028.
 - If `action` is "augment" or "augment_aggressive", proceed to T025b.
 - If trigger file is absent, log status="error" and halt. (FR-004, Plan Correction)
- [ ] T025b [US2] (Depends on T025a) **AUGMENTATION EXECUTION**: Apply data augmentation via **functional-group-preserving edge dropout** (non-ester bonds only) and SMILES canonicalization.
 - **Algorithm**: Use RDKit to identify ester bonds (C(=O)O pattern) and mask only non-ester bonds with a dropout rate of `0.2`.
 - **Constraint**: DO NOT implement bond rotation logic here.
 - Log chemical validity checks.
 - **Output**: Save the augmented dataset to a temporary file `data/processed/augmented_graph_dataset.csv`. (FR-004, Plan Correction)
- [ ] T025c [US2] (Depends on T025b) **AUGMENTATION VALIDATION & SAVE**: Validate chemical integrity of the augmented dataset.
 - **Output**: Save the final dataset to `data/processed/final_dataset.csv` with checksums.
 - Measure runtime and log to `data/reports/augmentation_timing.json`. **Constraint**: If duration > 30 minutes, log a FAIL status; otherwise PASS.
 - Log the action to `data/processed/augmentation_log.json`. (FR-004, US-2 Scenario 3)
- [X] T025d_new [US2] (Depends on T025c) **BOND ROTATION REJECTION DOCUMENTATION**: Generate `data/reports/bond_rotation_rejection_log.json` explicitly stating that "bond rotation and atom masking" is chemically invalid for degradation pathways and is NOT implemented. Confirm that the Constitution VII robustness requirement is satisfied by the "aggressive edge dropout" (T025b) and Leave-One-Out validation. (Constitution VII, FR-004 Traceability)
- [ ] T028 [US2] (Depends on T017b OR T025c) **TRAINING**: Implement `train.py`:
 - Check for existence of `data/processed/final_dataset.csv`.
 - **Dependency Logic**: This task runs after T017b (if n>150) or T025c (if n<=150).
 - Implement training loop with 5-fold cross-validation (or leave-one-out if n < 50) and random seed pinning.
 - Report mean macro-F1 and convergence check (loss delta < 5% over last 5 epochs).
 - **Checkpoint**: Save model to `data/reports/model_best.pth`. (FR-003, US-2 Scenario 1)
- [ ] T029 [US2] (Depends on T028) Implement `model.py`: Compute feature importance scores using Integrated Gradients on the trained model. **Output**: Save to `data/reports/ig_attribution_maps.json` with schema: `[{"atom_index": int, "feature_importance": float, "normalized_score": float}]`. (FR-005)
- [ ] T030 [US2] (Depends on T029) Implement `evaluate.py`: Calculate percentage of hydrolysis cases where ester bonds are in top `THRESHOLD_TOP_PERCENT` (default 10) of attribution scores. **Validation**: Compare this percentage against a null distribution generated by shuffling motif attributions multiple times using an empirical p-value calculation. **Threshold**: `PERCENTAGE_THRESHOLD = 0.90`. Generate `data/reports/ester_attribution_check.json` with keys `{"percentage": float, "threshold": 0.90, "p_value_null_comparison": float, "status": "PASS|FAIL"}`. (SC-005)
- [ ] T031 [US2] (Depends on T030) Implement `evaluate.py`: Save model checkpoints, validation metrics (macro-F1), and IG attribution maps to `data/reports/`. (FR-003, FR-005)
- [ ] T032 [US2] (Depends on T031) Implement `evaluate.py`: Generate test-set predictions using the trained model; save predictions to `data/reports/test_predictions.json` for downstream validation. (FR-007)
- [ ] T033 [US2] (Depends on T017b OR T017c) Add logging for training progress, validation scores, augmentation stats, and runtime constraints in `code/train.py`

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

- [ ] T037 [US3] (Depends on T031) **SCIENTIFIC VALIDATION (Permutation Test - Shuffling)**: Implement `evaluate.py`: Perform Permutation Test by **shuffling input motifs** (as per FR-006) using 'Motif-Shuffling' as the specific mechanism.
 - **Motif Extraction**: Use RDKit to find subgraphs of small sizes.
 - **Statistic Definition**: `observed_stat` = mean macro-F1 score drop between original model and motif-shuffled model.
 - **Null Distribution**: Generate `1000` permutations to ensure statistical robustness.
 - **Mapping**: Explicitly document that 'Motif-Shuffling' implements the 'shuffling input motifs' requirement from US-3 Scenario 1.
 - Generate `data/reports/permutation_test_results.json` with schema: `{'bins': [float], 'counts': [int], 'observed_stat': float, 'p_value': float}` (FR-006, SC-002, US-3 Scenario 1)
- [ ] T037b [US3] (Depends on T037) **LABEL-SHUFFLING VALIDATION**: Implement `evaluate.py`: Perform a label-shuffling permutation test to validate global model significance. **Note**: This is a complementary test and does NOT satisfy FR-006's specific motif-shuffling requirement (handled by T037). (Complementary to T037)
- [ ] T038 [US3] (Depends on T031) **CONSTITUTIONAL VALIDATION (χ²)**: Implement `evaluate.py`: Implement χ² Discretization Protocol.
 - **Binning**: Apply 'quantile-based binning' (top quantile vs rest) on absolute Integrated Gradients scores.
 - **Tie-Breaking**: If a score is at a low percentile threshold, assign it to the 'Low' bin.
 - **Validation**: Log bin counts and verify distribution is uniform before proceeding.
 - Generate `data/reports/chisquare_validation.csv` with schema: columns `['bin_id', 'observed_count', 'expected_count', 'chi_sq_contrib']` and a summary row `['TOTAL',...,..., 'chi_sq_stat']`. (Constitution VI, Plan Complexity Tracking)
- [ ] T039 [US3] (Depends on T031) Implement `evaluate.py`: Aggregate feature importances to identify a small set of top structural motifs and their correlation with degradation types. **Logic**: Group by motif pattern, calculate mean importance, rank by mean importance, select top few. (FR-007)
- [ ] T040 [US3] (Depends on T031) Implement `evaluate.py`: Generate final report in `data/reports/` including p-values, motif list, and confidence flags (FR-007). **Content**: `p_value`, `motif_list` (top 3-5), `confidence_flags` (predictions < 0.6).
- [ ] T041 [US3] (Depends on T031) Implement `evaluate.py`: Add logic to flag predictions with confidence < `0.6` as "low confidence" in the report (US-3 Acceptance Scenario 3, Plan: Data Exclusion)
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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1 (T017b/T017c output)
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
 - Developer B: User Story 2 (Model Training) - *Wait for T017b/T017c output*
 - Developer C: User Story 3 (Validation) - *Wait for T031 output*
3. Stories complete and integrate independently

---

## Methodological Corrections

**⚠️ MANDATORY INSTRUCTIONS FOR IMPLEMENTERS**

The following rules override any conflicting instructions in `spec.md` or previous drafts. These are the **only** valid instructions for this project:

1. **Data Handling Distinction**:
 - **Missing Labels**: Records missing 'degradation pathway' labels MUST be **FLAGGED** (saved to `data/raw/flagged_for_curation.csv`) for manual review, then excluded from the immediate training set. This satisfies FR-008 and US-1 Scenario 2.
 - **Missing Environmental Data (Default Path)**: Records missing environmental data (temp/pH/UV) MUST be **FLAGGED** (saved to `data/raw/flagged_env_data.csv`) and **EXCLUDED** from the training set to prevent confounding. This is the DEFAULT and ONLY scientific approach.
 - **Imputation Path (FR-002 Compliance)**: Imputation is **REJECTED** as methodologically flawed. T015c documents this rejection and creates a valid log artifact to satisfy the "flagging OR imputing" requirement by choosing "flagging" and documenting the decision.
2. **Augmentation Strategy**:
 - **T025b (Plan Correction)**: Implement 'functional-group-preserving edge dropout' (non-ester bonds only) and SMILES canonicalization. Skip if n > 150.
 - **T025d_new (Constitution VII)**: Bond rotation is **REJECTED** as chemically invalid. The Constitution VII robustness requirement is satisfied by the 'aggressive edge dropout' (T025b) and Leave-One-Out validation for n < 50.
 - **Bond Rotation Removal**: The Spec's requirement for 'bond rotation and atom masking' is chemically invalid for degradation pathways. Do NOT implement this method. (Documented in T025d_new).
 - **Verification**: T025b MUST include a step to verify that NO bond rotation logic was applied.
3. **Statistical Validation**:
 - **T037 (Scientific)**: Implement 'shuffling input motifs' (as per FR-006) using 'Motif-Shuffling' as the specific mechanism. This is the primary validation method for motif significance.
 - **T038 (Constitutional)**: Implement χ² Discretization Protocol to satisfy Constitution Principle VI. This is the complementary validation method.
4. **Thresholds**: For SC-004, trigger a warning if n < 150. For SC-005, use `THRESHOLD_TOP_PERCENT` (default 10) and `PERCENTAGE_THRESHOLD` (default 0.90) for verification. For US-3, use `CONFIDENCE_THRESHOLD` (default 0.6).

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
- **CRITICAL**: Records with missing environmental data (temp/pH/UV) MUST be FLAGGED then EXCLUDED (DEFAULT PATH).
- **CRITICAL**: Records with missing labels MUST be FLAGGED for curation before exclusion (FR-008).
- **CRITICAL**: GNN must run on CPU only; no CUDA/GPU dependencies.
- **CRITICAL**: Edge Dropout (T025b) is the default augmentation. Bond Rotation is INVALID and NOT IMPLEMENTED.
- **CRITICAL**: χ² Test (T038) is Constitutional/Complementary; Permutation Test (T037) is Scientific/Primary.
- **CRITICAL**: Confidence threshold < `0.6` is MANDATORY for flagging low-confidence predictions (US-3 Scenario 3, Plan).
- **CRITICAL**: T015c exists to satisfy FR-002 traceability by documenting the rejection of invalid methods.
- **CRITICAL**: T017a, T017b, T017c atomize the power analysis logic for deterministic execution.
- **CRITICAL**: T025a, T025b, T025c atomize the augmentation logic for deterministic execution.
- **CRITICAL**: T025d_new documents the rejection of bond rotation.
- **CRITICAL**: T037 is the primary satisfier of FR-006; T037b is complementary.