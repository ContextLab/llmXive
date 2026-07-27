# Tasks: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

**Input**: Design documents from `/specs/001-predict-reaction-yields-from-spectra/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**CRITICAL SCOPE ALIGNMENT NOTE**:
This project has pivoted from "Predicting Reaction Yields" (as defined in `spec.md`) to "Predicting Normalized DFT Total Molecular Energy" (as defined in `plan.md`) due to the unavailability of verified real-world datasets containing paired (Reaction SMILES, Experimental Yield, Spectrum) data.
- **Impact**: Functional Requirements FR-001 through FR-011 and Success Criteria SC-001 through SC-005 in `spec.md` that reference "yield" are **currently invalid** for the proposed plan.
- **Action**: **Task T000** performs the mandatory "Spec Amendment" to formally update `spec.md` to reflect this pivot, establishing the Plan's scope as the new Spec truth. All subsequent tasks implement the **Plan's** pivot (DFT Energy). A formal "Pivot & Limitation Report" (Task T020c) will be generated to document the resolution for the research review stage.

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., User Story 1, User Story 2)
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

- [ ] T000 [P] **Spec Amendment: Pivot to DFT Energy**. **Logic**: 1) Read `plan.md` Summary to confirm pivot to "Normalized DFT Total Molecular Energy". 2) Update `spec.md` to reflect this pivot: Amend FR-001, FR-002, FR-010, and SC-001 to SC-005 to reference "DFT Energy" instead of "Yield". 3) Add a new "Scope Note" section to `spec.md` explicitly stating the pivot and the use of simulated data. 4) Commit this change as a formal "Spec Amendment" to satisfy the Single Source of Truth principle (Constitution Principle IV) before any implementation begins. **Deliverables**: Updated `spec.md` with amended FRs/SCs and Scope Note.
- [ ] T001 Create project structure per implementation plan (`src/`, `data/`, `tests/`, `state/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (PyTorch CPU, scikit-learn, RDKit, pandas, numpy, matplotlib, seaborn, pyyaml)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `src/utils/seeds.py` for deterministic random seed management (global seed, PyTorch, NumPy, Python)
- [X] T005 [P] Implement `src/utils/state_manager.py` to update project state hashes and timestamps (Principle V)
- [X] T006 [P] Create `src/config/defaults.yaml` defining hyperparameters (LR=1e-3, batch=32, epochs=10, early stopping patience) and **attention visualization thresholds** (default and sensitivity range) as required by FR-009.
- [ ] T007 Implement `src/utils/validators.py` for schema validation helpers (YAML/JSON)
- [ ] T008 Create `contracts/` directory with `dataset.schema.yaml` and `model_output.schema.yaml` based on `data-model.md`
- [ ] T009 Implement `src/cli/main.py` entry point with `--update-state` flag and basic argument parsing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw spectral/structural data, resample to fixed grids, normalize, encode conditions, and split by reaction template to prevent leakage. **Note**: Target variable is now "normalized DFT total molecular energy" per Plan Summary (post-T000).

**Independent Test**: The pipeline can be executed on a subset of simulated DFT data (MolSpectra), producing three distinct CSV/Parquet files (train, val, test) and a log confirming the absence of overlapping reaction templates across splits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [User Story 1] Unit test for spectral resampling logic in `tests/unit/test_resampling.py`
- [X] T011 [P] [User Story 1] Unit test for reaction template extraction and leakage check in `tests/unit/test_splitting.py`
- [X] T012 [P] [User Story 1] Integration test for full pipeline end-to-end on dummy data in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [User Story 1] Implement `src/data/ingestion.py` to fetch primary training data and check for independent experimental dataset. **Logic**: 1) Fetch the **primary** training dataset: Simulated DFT data (MolSpectra) from HuggingFace repository ID `MolSpectra/dft-spectra-energies-v1`. This fetch MUST occur. 2) If the fetch of the primary training data fails (e.g., network error or missing HuggingFace mirror), raise an exception immediately (DO NOT fall back to synthetic; the simulated data IS the primary source here). 3) Attempt to locate an independent experimental dataset for validation. If found, log status='found'; if not (expected), log status='missing' in `data/validation_status.json`. 4) Log the data source used, the exact dataset ID, and the checksum in `data/ingestion_log.json`. 5) If independent dataset is 'found', flag it for T043; if 'missing', document the limitation for T010c. **Deliverables**: Create/Write `data/validation_status.json` (schema: `{status: string, timestamp: string}`) and `data/ingestion_log.json` (schema: `{source: string, dataset_id: string, checksum: string, timestamp: string}`).
- [ ] T014 [P] [User Story 1] Implement `src/data/resampling.py`: Resampling IR/Raman to a standard mid-infrared range (starting from the lower wavenumber limit) and NMR to a defined chemical shift range. (or schema-defined ranges from MolSpectra) to fixed grids, unit variance normalization. Ensure target variable is "normalized DFT total molecular energy".
- [ ] T015 [P] [User Story 1] Implement `src/data/encoding.py`: Encoding reaction conditions (solvent, catalyst, temperature) as one-hot or embedding vectors. **Note**: These MUST be used as features in the split logic (T017a) to prevent confounding. **Dependency**: This task MUST complete before T017a.
- [ ] T016 [P] [User Story 1] Implement `src/data/template_extraction.py`: Reaction template extraction (substructure at reaction center) using RDKit.
- [ ] T017a [User Story 1] Implement `src/data/splitting.py`: **Reaction Template Splitting**. **Algorithm**: 1) Shuffle samples. 2) Group by `template_id`. 3) Assign groups to Train/Val/Test to maintain **strict /15/15 ratio**. 4) **Small Dataset Handling**: If a template appears in only 1 sample, assign it to the Train set by default to avoid stratification errors. 5) Verify zero overlap of `template_id` between Train, Val, and Test. If overlap > 0, raise an error and halt the pipeline (do NOT fall back to weaker splitting methods). Explicitly use the encoded reaction conditions (from T015) as features during the split to prevent confounding, as required by FR-011. **Deliverables**: 1) Generate `data/processed/split_indices.parquet` with schema `{split: string, index: int}`. 2) Generate `data/artifacts/split_manifest.json` with schema `{train_count: int, val_count: int, test_count: int, overlap_check: boolean}`. **Constraint**: If overlap > 0, raise an error and halt the pipeline. **Dependency**: T015.
- [ ] T017b [User Story 1] Implement `src/data/verification.py`: **Reaction Template Overlap Verification**. **Logic**: Verify that the split produced by T017a has zero overlap of reaction templates between train, val, and test sets. Additionally, verify that reaction conditions were explicitly used in the split logic (per FR-011) by checking the split manifest or code artifacts. If overlap > 0 or conditions not used, raise an error and halt the pipeline. This is a mandatory verification step.
- [ ] T018 [User Story 1] Implement `src/data/loaders.py`: PyTorch `Dataset` classes for `ReactionSample` handling missing channels (masking). Target variable: normalized DFT total molecular energy.
- [ ] T019 [User Story 1] Create `data/` directory structure (`raw/`, `processed/`, `artifacts/`, `references/`) and implement checksum logging in `state/`.
- [X] T019b [User Story 1] Create `data/references/literature_values.csv` containing functional group frequencies. **Schema**: Columns must be `functional_group` (string), `min_wavenumber` (float), `max_wavenumber` (float), `unit` (string, e.g., "cm-1"). **Content**: Populate with standard functional group ranges (e.g., Carbonyl: -1750, O-H: -3600, N-H: -3500, C-H: lower frequency range) derived from standard chemical literature (Silverstein) directly in the task logic. **Note**: Do NOT fetch from NIST; use hardcoded values for self-containment.
- [ ] T020 [User Story 1] Add validation script to verify no scaffold leakage between splits and log results to `data/artifacts/leakage_report.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Attention-Based Yield Prediction Model Training (Priority: P2)

**Goal**: Implement and train the multi-head self-attention model combining spectra, fingerprints, and conditions on CPU. **Target**: Normalized DFT total molecular energy.

**Independent Test**: The training script executes successfully on a CPU-only environment, producing a saved model file and a log showing a decreasing validation loss over defined epochs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [User Story 2] Unit test for model architecture construction in `tests/unit/test_attention_net.py`
- [X] T022 [P] [User Story 2] Unit test for training loop logic (loss calculation, backprop) in `tests/unit/test_trainer.py`

### Implementation for User Story 2

- [ ] T023 [P] [User Story 2] Implement `src/models/baselines.py`: Fingerprint-only, Spectrum-only, and Condition-only baseline models. Target: normalized DFT total molecular energy.
- [ ] T024 [User Story 2] Implement `src/models/attention_net.py`: Multi-head self-attention network accepting concatenated spectral tensors, ECFP4 vectors, and condition embeddings. Target variable: normalized DFT total molecular energy; Loss function: MSE.
- [ ] T025 [User Story 2] Implement `src/models/trainer.py`: Training loop with Adam optimizer (learning rate), batch size 32, a limited number of epochs, early stopping on validation RMSE (of energy).
- [ ] T026 [User Story 2] Implement `src/models/checkpoint.py`: Checkpointing logic saving weights and config hash to `data/artifacts/`.
- [ ] T027 [User Story 2] Implement `src/cli/main.py` subcommand `train` to orchestrate data loading, model training, and logging.
- [ ] T028 [User Story 2] Add deterministic reproducibility check: re-run training with same seed and verify identical weights/metrics.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Evaluation and Interpretability Analysis (Priority: P3)

**Goal**: Evaluate against baselines, perform statistical tests, generate attention visualizations, and run permutation tests. **Target**: Normalized DFT total molecular energy.

**Independent Test**: The evaluation script runs on the test set, outputs RMSE/MAE/R² metrics, performs a paired t-test, and generates an attention heatmap.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [User Story 3] Unit test for metric calculation (RMSE, MAE, R²) in `tests/unit/test_metrics.py`
- [ ] T030 [P] [User Story 3] Unit test for paired t-test implementation in `tests/unit/test_statistics.py`

### Implementation for User Story 3

- [ ] T031 [P] [User Story 3] Implement `src/eval/metrics.py`: Compute RMSE, MAE, R² for attention model and all baselines against normalized DFT total molecular energy.
- [ ] T032 [User Story 3] Implement `src/eval/metrics.py`: Paired t-test on absolute errors (Attention vs. best baseline) with Bonferroni correction.
- [ ] T033a [User Story 3] Implement `src/eval/interpretability.py`: **Attention Weight Extraction**. Extract attention weights from the trained model for the test set.
- [ ] T033b [User Story 3] Implement `src/eval/interpretability.py`: **Heatmap Generation**. Generate heatmaps for each sample using the extracted weights.
- [ ] T033c [User Story 3] Implement `src/eval/interpretability.py`: **Sensitivity Analysis**. **Logic**: Read the default threshold and sensitivity range from `src/config/defaults.yaml` (as defined in T006). Perform sensitivity analysis over the defined range of thresholds. Generate a comparative sensitivity report. **Constraint**: Do NOT hardcode thresholds; the task must fail if config values are missing.
- [ ] T034 [User Story 3] Implement `src/eval/interpretability.py`: Correlation analysis between attention weights and energy residuals (controlling for fingerprints).
- [ ] T035 [User Story 3] Implement `src/eval/permutation.py`: Permutation test (shuffled energies) to verify R² < 0.05.
- [ ] T036 [User Story 3] Implement `src/cli/main.py` subcommand `eval` to run full evaluation suite and generate `data/artifacts/evaluation_report.json`.
- [ ] T037 [User Story 3] Implement `src/eval/interpretability.py`: **Literature Alignment Sanity Check**. **Logic**: Compare attention peaks against literature values from `data/references/literature_values.csv` (schema defined in T019b). **Metric**: Calculate the percentage of top 5 attention peaks falling within ±50 cm⁻¹ of literature values. **Constraint**: **Align with Plan**: This is a **secondary sanity check** (per Plan Evaluation Strategy). If the threshold (≥80%) is not met, log a WARNING in `data/artifacts/literature_check_report.json` but do NOT raise an error or fail the task. This aligns the implementation with the Plan's intent while preserving the Spec's metric definition for reporting. **Output**: Report a "Secondary Check" status (Pass/Fail/Warning).
- [ ] T043 [User Story 3] **Independent Experimental Validation**. **Logic**: 1) Read `data/validation_status.json` (from T013). 2) If status is 'found', load the independent dataset, run the trained model (T027) on it, and compute RMSE, MAE, R². Generate a "Independent Validation Report" comparing these results to the test set results to verify generalizability (FR-010). 3) If status is 'missing', log a "Skipped" status and document the limitation in `data/artifacts/fr010_limitation_phase5.json`. **Timing**: Run AFTER T027 (model training) and T036 (evaluation). **Dependency**: T013, T027, T036. **Note**: Moved from Phase 3 to Phase 5 to reflect dependencies.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` and `README.md`
- [ ] T039 Code cleanup and refactoring
- [ ] T040 Performance optimization across all stories (ensure CPU execution < 6 hours)
- [ ] T041 [P] Additional unit tests in `tests/unit/`
- [ ] T042 Run `quickstart.md` validation and update `research.md` with findings
- [ ] T010c [Phase N] **Document FR-010 Limitation**. **Logic**: Create `data/artifacts/fr010_limitation_report.json`. **Content**: 1) State that FR-010 (Independent Experimental Validation) cannot be satisfied due to the pivot to simulated DFT data. 2) Document the Plan's mitigation strategy: reliance on Structure-Only Baseline (T023) and Permutation Test (T035) and the new T010d (Circularity Mitigation) to address circularity. 3) Flag this as a required output for the research review stage. **Timing**: Run after T013 completes. **Dependency**: T013.
- [ ] T010d [User Story 1] **Circularity Mitigation & Baseline Validation**. **Logic**: Implement a rigorous validation step to satisfy the *intent* of FR-010 (preventing circular validation) within the DFT scope. 1) Train the Structure-Only Baseline (T023) on the same data. 2) Compare Attention Model (T024) vs. Structure-Only Baseline. 3) If the Attention Model does NOT significantly outperform the Structure-Only Baseline, flag the result as "Circular Validation Risk". 4) Document this comparison in `data/artifacts/circularity_mitigation_report.json`. **Timing**: Run after T013 and T023 (conceptually, but logic is defined here). **Dependency**: T013.
- [ ] T020e [Phase N] **Verify Target Variable Usage**. **Logic**: Run static analysis script `src/utils/verify_target.py` against `src/` to confirm all downstream tasks (T014, T015, T018, T023-T025, T031-T035) use the "normalized DFT total molecular energy" target. **Output**: `data/artifacts/target_verification.json`. **Timing**: Run AFTER T014, T015, T018, T020, T023, T024, T025, T031, T032, T033a, T033b, T033c, T034, T035, T037, T043 are completed and committed.
- [ ] T020c [Phase N] **Generate Pivot & Limitation Report**. **Content**: 1) Document the pivot from experimental yield to DFT energy (Spec vs Plan contradiction). 2) Explicitly state the limitation regarding FR-010 (Independent Experimental Validation) due to the pivot to simulated data (circular validation). 3) Aggregate results from `data/artifacts/target_verification.json` (generated by T020e) to confirm downstream tasks use the correct target. 4) Aggregate results from T010c and T010d to document the mitigation strategy. **Timing**: Run AFTER T000 (Spec Amendment), T010c, T010d, T043, and T020e are completed and committed. **Method**: Read `data/artifacts/target_verification.json` from T020e to confirm target usage.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on User Story 1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on User Story 2 model output

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (including T000 Spec Amendment)
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
- [Story] label maps task to specific user story for traceability (e.g., User Story 1)
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Hygiene**: All data loading tasks MUST fail loudly on missing real/simulated data; NO synthetic fallbacks allowed.
- **CPU Constraint**: Ensure all training tasks are optimized for CPU execution within 6 hours.
- **Scope Pivot**: All tasks assume the target variable is "normalized DFT total molecular energy" per Plan Summary, not "yield_percent" from Spec. T000 amends the Spec to reflect this.
- **Report Generation**: T020c (Pivot & Limitation Report) runs AFTER T000, T010c, T010d, T043, and T020e are completed and committed.
- **Split Logic**: T017a uses strict reaction template splitting to satisfy FR-002; T017b verifies zero overlap and condition usage; T017c is removed.
- **FR-011**: T015 and T017a ensure conditions are used in split logic.
- **FR-009**: T033c reads thresholds from config and performs sensitivity analysis.
- **FR-010**: T013 checks for independent dataset; T043 performs actual validation if found; T010c and T010d document the limitation and mitigation if missing.
- **Literature Check**: T037 is now a secondary check (warning log) per Plan, preserving Spec metric definition.
- **T013 Logic**: Reads status from T013; fetches simulated DFT data as primary training source; raises on network error for primary data. T013 also logs the status of the independent dataset check.
- **T015/T017a Dependency**: T015 is a blocking prerequisite for T017a.
- **T043 Location**: Moved to Phase 5 to reflect dependencies on T027 and T036.
- **Removed Tasks**: T017c (Scaffold Strictness Check) and T020d (Chi-square test) removed to align with Plan.
- **File Decomposition**: Tasks T014-T017b now target distinct files (`resampling.py`, `encoding.py`, `template_extraction.py`, `splitting.py`, `verification.py`) to ensure atomic executability.
- **T024-T026 Decomposition**: Tasks T024-T026 now target distinct files (`attention_net.py`, `trainer.py`, `checkpoint.py`).