# Tasks: Predicting Chemical Reaction Yields from Spectroscopic Data with Attention Mechanisms

**Input**: Design documents from `/specs/001-predict-reaction-yields-from-spectra/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**CRITICAL SCOPE ALIGNMENT NOTE**:
This project has pivoted from "Predicting Reaction Yields" (as defined in `spec.md`) to "Predicting Normalized DFT Total Molecular Energy" (as defined in `plan.md`) due to the unavailability of verified real-world datasets containing paired (Reaction SMILES, Experimental Yield, Spectrum) data.
- **Impact**: Functional Requirements FR-001 through FR-011 and Success Criteria SC-001 through SC-005 in `spec.md` that reference "yield" are **currently invalid** for the proposed plan.
- **Action**: The tasks below implement the **Plan's** pivot (DFT Energy). A formal "Pivot & Limitation Report" (Task T020c) will be generated to document this contradiction for the research review stage. The Spec must be updated to reflect this pivot or the Plan must be rejected.

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

- [ ] T001 Create project structure per implementation plan (`src/`, `data/`, `tests/`, `state/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (PyTorch CPU, scikit-learn, RDKit, pandas, numpy, matplotlib, seaborn, pyyaml)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `src/utils/seeds.py` for deterministic random seed management (global seed, PyTorch, NumPy, Python)
- [ ] T005 [P] Implement `src/utils/state_manager.py` to update project state hashes and timestamps (Principle V)
- [ ] T006 [P] Create `src/config/defaults.yaml` defining hyperparameters (LR=1e-3, batch=32, epochs=10, early stopping patience)
- [ ] T007 Implement `src/utils/validators.py` for schema validation helpers (YAML/JSON)
- [ ] T008 Create `contracts/` directory with `dataset.schema.yaml` and `model_output.schema.yaml` based on `data-model.md`
- [ ] T009 Implement `src/cli/main.py` entry point with `--update-state` flag and basic argument parsing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw spectral/structural data, resample to fixed grids, normalize, encode conditions, and split by scaffold to prevent leakage. **Note**: Target variable is now "normalized DFT total molecular energy" per Plan Summary.

**Independent Test**: The pipeline can be executed on a subset of simulated DFT data (MolSpectra), producing three distinct CSV/Parquet files (train, val, test) and a log confirming the absence of overlapping scaffolds across splits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [User Story 1] Unit test for spectral resampling logic in `tests/unit/test_preprocessing.py`
- [X] T011 [P] [User Story 1] Unit test for scaffold extraction and leakage check in `tests/unit/test_data_splitting.py`
- [X] T012 [P] [User Story 1] Integration test for full pipeline end-to-end on dummy data in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [User Story 1] Implement `src/data/ingestion.py` to fetch data. **Logic**: 1) Attempt to fetch verified real experimental data from a canonical source (e.g., NIST/ZINC). 2) If the fetch fails with a 404 or "source unavailable" error, explicitly switch to the MolSpectra simulated pipeline and log the pivot. 3) If the fetch fails due to network error or timeout, raise an exception to trigger the execution stage's re-try logic (DO NOT fall back to synthetic). 4) Log the data source used and checksum in `state/`. 5) If an independent experimental dataset is found (see T013b), flag it for validation but DO NOT use it for training. <!-- FAILED: unspecified -->
- [ ] T013b [User Story 1] Implement `src/data/ingestion.py` check for independent experimental dataset (FR-010). **Logic**: Attempt to locate and fetch the independent validation dataset. If successful, enable the validation pipeline (T043). If it fails (source unreachable), trigger the pivot to simulated data and ensure the limitation is documented in T020c. This task runs AFTER T013's initial fetch attempt to determine availability. <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
- [X] T014 [P] [User Story 1] Implement `src/data/preprocessing.py`: Resampling IR/Raman to a standard mid-infrared range (starting from the lower wavenumber limit) and NMR to –10 ppm (or schema-defined ranges from MolSpectra) to fixed grids, unit variance normalization. Ensure target variable is "normalized DFT total molecular energy".
- [X] T015 [User Story 1] Implement `src/data/preprocessing.py`: Encoding reaction conditions (solvent, catalyst, temperature) as one-hot or embedding vectors. **Note**: These MUST be used as features in the split logic (T017) to prevent confounding.
- [X] T016 [User Story 1] Implement `src/data/preprocessing.py`: Reaction template extraction (substructure at reaction center) using RDKit.
- [X] T017 [User Story 1] Implement `src/data/preprocessing.py`: Splitting logic. **Algorithm**: Implement **scaffold-based splitting** (molecular scaffolds) as mandated by the Plan's Summary and Complexity Tracking. This supersedes the Spec's "reaction template" for this project. Ensure zero scaffold overlap between train/val/test. Explicitly use the encoded reaction conditions (from T015) as features during the split to prevent confounding, as required by FR-011.
- [ ] T018 [User Story 1] Implement `src/data/loaders.py`: PyTorch `Dataset` classes for `ReactionSample` handling missing channels (masking). Target variable: normalized DFT total molecular energy.
- [ ] T019 [User Story 1] Create `data/` directory structure (`raw/`, `processed/`, `artifacts/`) and implement checksum logging in `state/`.
- [ ] T020 [User Story 1] Add validation script to verify no scaffold leakage between splits and log results to `data/artifacts/leakage_report.json`.
- [ ] T020d [User Story 1] Generate a "Confounding Prevention Report" in `data/artifacts/`. **Content**: Verify that the encoded reaction conditions (from T015) were explicitly used as features during the split logic (T017) to prevent confounding, as mandated by FR-011. Include a statistical check or log confirming this usage.
- [ ] T020c [User Story 1] Generate a "Pivot & Limitation Report" in `data/artifacts/`. **Content**: 1) Document the pivot from experimental yield to DFT energy (Spec vs Plan contradiction). 2) Explicitly state the limitation regarding FR-010 (Independent Experimental Validation) due to the pivot to simulated data (circular validation). 3) Verify and list all downstream tasks (T014, T015, T018, T023-T025, T031-T035) to confirm they use the "normalized DFT total molecular energy" target in their **implementation** (code check), not just specification. **Timing**: Run AFTER T014, T015, T018, T020, and T020d to ensure the pivot decision is finalized and implementation is verifiable.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Attention-Based Yield Prediction Model Training (Priority: P2)

**Goal**: Implement and train the multi-head self-attention model combining spectra, fingerprints, and conditions on CPU. **Target**: Normalized DFT total molecular energy.

**Independent Test**: The training script executes successfully on a CPU-only environment, producing a saved model file and a log showing a decreasing validation loss over defined epochs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [User Story 2] Unit test for model architecture construction in `tests/unit/test_attention_net.py`
- [ ] T022 [P] [User Story 2] Unit test for training loop logic (loss calculation, backprop) in `tests/unit/test_trainer.py`

### Implementation for User Story 2

- [ ] T023 [P] [User Story 2] Implement `src/models/baselines.py`: Fingerprint-only, Spectrum-only, and Condition-only baseline models. Target: normalized DFT total molecular energy.
- [ ] T024 [User Story 2] Implement `src/models/attention_net.py`: Multi-head self-attention network accepting concatenated spectral tensors, ECFP4 vectors, and condition embeddings. Target variable: normalized DFT total molecular energy; Loss function: MSE.
- [ ] T025 [User Story 2] Implement `src/models/trainer.py`: Training loop with Adam optimizer (learning rate), batch size 32, a limited number of epochs, early stopping on validation RMSE (of energy).
- [ ] T026 [User Story 2] Implement `src/models/trainer.py`: Checkpointing logic saving weights and config hash to `data/artifacts/`.
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
- [ ] T033 [User Story 3] Implement `src/eval/interpretability.py`: Extract attention weights and generate heatmaps. **Mechanism**: Hardcode thresholds as {%, 10%, 15%} as required by FR-009. Loop over these thresholds to generate separate heatmaps and a comparative sensitivity report. Ignore config file values for this specific metric to ensure compliance with the spec.
- [ ] T034 [User Story 3] Implement `src/eval/interpretability.py`: Correlation analysis between attention weights and energy residuals (controlling for fingerprints).
- [ ] T035 [User Story 3] Implement `src/eval/permutation.py`: Permutation test (shuffled energies) to verify R² < 0.05.
- [ ] T036 [User Story 3] Implement `src/cli/main.py` subcommand `eval` to run full evaluation suite and generate `data/artifacts/evaluation_report.json`.
- [ ] T037 [User Story 3] Implement `src/eval/interpretability.py`: Literature alignment sanity check. **Logic**: Compare attention peaks against literature values for functional groups. **Note**: Per the Plan, this is a **secondary sanity check**, NOT a pass/fail metric. Generate a report of the alignment statistics (e.g., % of peaks within ±50 cm⁻¹) but DO NOT enforce a hard success criterion that contradicts the Plan.
- [ ] T043 [User Story 3] Implement `src/eval/validate_independent.py`: Independent Experimental Validation. **Logic**: If an independent experimental dataset was found (T013b), load it, run the trained model (T027) on it, and compute RMSE/MAE/R². Generate a "Independent Validation Report" comparing these results to the test set results to verify generalizability (FR-010). If no independent dataset was found, log a "Skipped" status and document the limitation in T020c. **Timing**: Run AFTER T027 (model training) and T036 (evaluation).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` and `README.md`
- [ ] T039 Code cleanup and refactoring
- [ ] T040 Performance optimization across all stories (ensure CPU execution < 6 hours)
- [ ] T041 [P] Additional unit tests in `tests/unit/`
- [ ] T042 Run `quickstart.md` validation and update `research.md` with findings

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
- [Story] label maps task to specific user story for traceability (e.g., User Story 1)
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Hygiene**: All data loading tasks MUST fail loudly on missing real/simulated data; NO synthetic fallbacks allowed.
- **CPU Constraint**: Ensure all training tasks are optimized for CPU execution within 6 hours.
- **Scope Pivot**: All tasks assume the target variable is "normalized DFT total molecular energy" per Plan Summary, not "yield_percent" from Spec.
- **Report Generation**: T020c (Pivot & Limitation Report) runs AFTER T014, T015, T018, T020, and T020d to ensure the pivot decision is finalized and implementation is verifiable.
- **Split Logic**: T017 uses Plan's "scaffold-based splitting" (stricter) over Spec's "reaction template".
- **FR-011**: T020d verifies conditions are used in split logic.
- **FR-009**: T033 hardcodes thresholds as {5%, 10%, 15%} and ignores config.
- **FR-010**: T013b checks for independent dataset; T043 performs actual validation if found.
- **Literature Check**: T037 is a secondary sanity check, not a hard pass/fail.
- **T013 Logic**: Attempt fetch; if 404/unavailable, pivot; if network error, raise.