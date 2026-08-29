# Tasks: Predicting Molecular Excitation Wavelengths from SMILES with Graph Neural Networks

**Input**: Design documents from `/specs/001-predicting-molecular-excitation-waveleng/`
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

- [ ] T001a [P] Create project directory structure: Create directories `data/raw`, `data/processed`, `code`, `tests`, `docs` in `projects/PROJ-379-predicting-molecular-excitation-waveleng/`
- [X] T001b [P] Create `requirements.txt` with pinned versions: `rdkit==2023.9.5`, `torch==2.1.0+cpu`, `torch-geometric==2.4.0`, `pandas==2.1.0`, `scikit-learn==1.3.0`, `numpy==1.24.0`, `pyyaml==6.0.1`, `pytest==7.4.0`
- [ ] T001c [P] Create `README.md` with Quickstart section: Include instructions for environment setup, data fetching, and running the pipeline end-to-end

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Create `.flake8` and `pyproject.toml` with black configuration for linting and formatting
- [X] T003 Implement `code/utils.py` with RDKit parsing helpers, logging setup, and CPU-only device configuration
- [X] T004 [P] Create data directory structure (`data/raw/`, `data/processed/`) and create empty `data/checksums.txt`
- [X] T005 Implement `code/hash_artifacts.py` to compute content hashes for artifacts and update `state/projects/PROJ-379-predicting-molecular-excitation-waveleng.yaml` (keys: `artifact_hashes`, `updated_at`) (Constitution V)
- [X] T006 Define Pydantic models `Molecule` (fields: `smi`, `lambda_max`, `scaffold_id`) and `Scaffold` in `code/models.py`
- [X] T007a [P] [Foundational] Implement `code/verify_accuracy_gate.py`: Execute Reference-Validator logic on dataset URLs (PubChem/SDBS) BEFORE ingestion. Verify the presence of `lambda_max_exp` column. Raise `FileNotFoundError` if validation fails. (Constitution II, FR-001). **This task blocks Phase 3.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw UV-Vis spectral data, parse SMILES to graphs, and produce a clean, scaffold-split dataset.

**Independent Test**: The pipeline can be fully tested by running the ingestion script on a sample subset and verifying that the output CSV contains valid SMILES, corresponding λmax values, and scaffold IDs, with no duplicate structures or missing values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [P] [US1] Contract test for data ingestion output schema in `tests/test_ingest.py`: Assert output columns are exactly `["smi", "lambda_max", "scaffold_id"]` with types `str`, `float`, `str`

### Implementation for User Story 1

- [X] T008 [US1] Implement `code/ingest.py`:
 1. **Primary Fetch**: Attempt to ingest raw UV-Vis data directly from **PubChem** (via `pubchempy` or official API) or **SDBS** (via official FTP/URL) as mandated by FR-001.
 2. **Fallback**: Only if primary sources fail, attempt `datasets.load_dataset("zjunlp/UV-Vis-ML")` as a secondary source.
 3. **Verify**: Check the dataset contains the `lambda_max_exp` column; raise error if missing.
 4. Parse SMILES, validate with RDKit, retain median λmax for duplicates.
 5. Implement chunked loading to ensure <7GB RAM usage.
 6. Save cleaned output to `data/processed/cleaned.csv` (NOT `data/raw`).
 7. **Enforce**: No synthetic fallback allowed; pipeline must fail loud on data issues.
- [X] T009 [US1] Implement `code/validate_data.py`: Data Validity Gate to check for `lambda_max_exp` column. If only computed values exist, **reframe SC-001** to "prediction of computed values" and log the limitation explicitly; do NOT silently reduce validity.
- [ ] T010 [US1] Implement `code/split.py`: Generate Bemis-Murcko scaffolds and split data into train/val/test using a **majority** training split with balanced validation and test sets. **Explicitly verify** that no scaffold appears in more than one split before writing indices. Output split indices (train_idx, val_idx, test_idx) to `data/processed/split_indices.json` (FR-002, Constitution VII).
- [ ] T010.5 [US1] Implement `code/merge_split.py`: Combine cleaned data from T008 and split indices from T010 into a single `data/processed/train_val_test.csv` with scaffold IDs, ready for model training (FR-001).
- [X] T011 [US1] Add logging for data ingestion, conflict resolution, and split statistics in `code/ingest.py`, `code/split.py`, and `code/merge_split.py`
- [X] T033 [US1] Implement streaming fallback for large datasets in `code/ingest.py`: Add logic to use `datasets.load_dataset(..., streaming=True)` if the initial non-streaming load fails due to memory constraints, ensuring the full real dataset is processed in chunks rather than falling back to synthetic data.
- [X] T034 [US1] Enforce "fail loud" policy in `code/ingest.py`: Remove any `try/except` blocks that catch download errors and substitute `generate_synthetic_*()` or `mock_*()` data; ensure any real fetch failure raises a distinct exception to halt the pipeline.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Evaluation (Priority: P2)

**Goal**: Train a lightweight GNN and baseline linear model, evaluate performance, and ensure CPU feasibility.

**Independent Test**: The training job can be tested by executing the training script on a fixed random seed and verifying that the model converges (loss decreases) and produces a test MAE and R² score in the expected range.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US2] Unit test for GNN architecture parameter count (<1M) in `tests/test_model.py`
- [X] T013 [P] [US2] Integration test for training loop convergence and artifact generation in `tests/test_train.py`

### Implementation for User Story 2

- [X] T014 [US2] Implement `code/model.py`: Define MPNN GNN (-3 layers, <1M params) and ECFP+Ridge Regression baseline (FR-003, FR-004)
- [X] T015 [US2] Implement `code/train.py`: Training loop with CPU-only execution, early stopping, fixed seed, and output `model.pt` (FR-003)
- [ ] T015b [US2] Implement `code/timing_logger.py`: Measure and log total wall-clock time of the pipeline (ingest to evaluate) to `data/processed/timing.json`. Verify compliance with SC-002 (≤6 hours) and raise warning if exceeded.
- [X] T016 [US2] Implement `code/evaluate.py`:
 1. Compute MAE, R².
 2. Perform Wilcoxon signed-rank test against baseline.
 3. **Calculate and report 95% confidence interval** for the MAE difference.
 4. **Apply Decision Logic**: If `p < 0.05` AND `MAE < 30` then `sc001_status = "PASS"`, else `sc001_status = "FAIL"`.
 5. Write partial results to `data/processed/metrics_partial.json` with keys: `mae`, `r2`, `wilcoxon_p_value`, `confidence_interval_95`, `sc001_status` (SC-001, FR-004)
- [X] T017 [P] [US2] Test task for SC-001 logic: Write `tests/test_evaluate.py` to verify that `sc001_status` and `confidence_interval_95` in `metrics_partial.json` are correctly calculated (F001)
- [ ] T018 [US2] Implement power analysis logic in `code/evaluate.py` to verify test set n≥50; append power analysis results (n, effect size, power_status) to `data/processed/power_analysis.json`
- [X] T019 [US2] Enforce n≥50 constraint: If test set size n < 50, halt execution and log error in `code/evaluate.py` to prevent downstream execution with insufficient power (SC-001)
- [X] T020 [US2] Add versioning step in `code/train.py` to generate hashes for `model.pt` and update `state/` YAML
- [X] T035 [US2] Add early stopping trigger in `code/train.py`: Implement logic to halt training if loss does not decrease for `patience` epochs, logging the trigger event to prevent infinite loops on CPU.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Attribution and Sensitivity Analysis (Priority: P3)

**Goal**: Analyze feature importance, perform sensitivity analysis on thresholds, and detect collinearity/redundancy.

**Independent Test**: The attribution script can be tested by running it on a representative subset of test molecules and verifying that it outputs a ranked list of contributing atoms/bonds for each molecule.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US3] Contract test for attribution output format in `tests/test_explain.py`
- [X] T022 [P] [US3] Integration test for sensitivity sweep and collinearity flags in `tests/test_sensitivity.py`: Verify MAE thresholds, 30, 40, 50, 60 nm are swept and collinearity flag logic is correct.

### Implementation for User Story 3

- [ ] T023 [US3] Implement `code/collinearity_check.py`: Calculate Pearson r for ECFP bits (flag if ≥0.9) and latent cosine similarity for GNN subgraphs (flag if >0.9), and generate redundancy masks for flagged subgraphs (FR-007). Output to `data/processed/redundancy_masks.json` with structure `{ "molecule_id": [0, 1, 0...] }` (mask array)
- [X] T036 [US3] Add subgraph redundancy aggregation in `code/collinearity_check.py`: Implement logic to aggregate subgraphs with latent cosine similarity > 0.9 and mask their individual attribution weights to prevent spurious independent effect claims (FR-007).
- [ ] T024 [US3] Implement `code/explain.py`: Perform GNNExplainer or gradient-based attribution on test set to generate **raw attribution** weights. Output to `data/processed/raw_attribution.json` (FR-005).
- [ ] T025 [US3] Apply and verify masking:
 1. Read raw attribution from T024 and redundancy masks from T023.
 2. Apply masks to raw attribution weights.
 3. Verify masking occurred by comparing masked vs. unmasked weights.
 4. Save final masked attribution to `data/processed/masked_attribution.json` (FR-007)
- [ ] T026 [US3] Implement `code/sensitivity.py`:
 1. Sweep MAE decision cutoffs using specific nanometer thresholds: **20, 30, 40, 50, 60 nm** (derived from US3 acceptance scenarios).
 2. Verify that the sweep covers these exact thresholds.
 3. Report variation in error rates (FR-006)
- [ ] T026b [US3] Generate Sensitivity Report: Create `data/processed/sensitivity_report.csv` and/or `sensitivity_plot.png` summarizing the error rate variation across thresholds. Ensure this artifact satisfies SC-004 requirements.
- [ ] T027 [US3] Implement `code/analyze_results.py`: Aggregate metrics from T016, power status from T018, collinearity flags and redundancy masks from T023/T036, and masked attribution from T025 into a single `data/processed/metrics.json` (SSoT). Ensure keys: `mae`, `r2`, `wilcoxon_p_value`, `confidence_interval_95`, `sc001_status`, `collinearity_flags`, `redundancy_masks`, `power_status`, `attribution_results` (Constitution IV, FR-007)
- [ ] T028a [P] [US3] Generate `quickstart.md` in `projects/PROJ-379-predicting-molecular-excitation-waveleng/specs/001-predicting-molecular-excitation-waveleng/`: Include instructions for environment setup, data fetching, and running the pipeline end-to-end.
- [ ] T029b [P] Documentation: Update `README.md` with instructions for interpreting feature attribution and masked attribution results (distinct from T028a).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029a [P] Documentation: Update `README.md` "Quickstart" section with instructions for running the full pipeline and interpreting `metrics.json`
- [X] T030a [P] Refactor: Extract validation logic in `code/ingest.py` into a separate function `validate_molecule(smiles)` to improve modularity
- [X] T030b [P] Refactor: Reduce cyclomatic complexity of `code/split.py` to <10 by extracting scaffold generation logic into a helper function
- [X] T031a [P] Performance: Optimize data loading in `code/ingest.py` by using multiprocessing to reduce loading time to <30s for A large set of molecules
- [ ] T031b [P] Performance: Measure baseline graph construction overhead in `code/utils.py` and implement caching of RDKit objects to target a [deferred] reduction in overhead relative to the measured baseline.
- [ ] T032 [P] Code cleanup: Remove unused imports and fix linting errors across `code/`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained model from US2

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

### Explicit Task Dependencies

- **T007a** (Verify Accuracy Gate) blocks **T008** (Ingest).
- **T010.5** depends on **T008** (cleaned data) and **T010** (split indices).
- **T025** depends on **T024** (raw attribution) and **T023** (masks).
- **T027** depends on **T016**, **T018**, **T023**, **T024**, **T025**, and **T026**.
- **T029b** and **T028a** are parallel-safe as they target distinct files (`README.md` vs `quickstart.md`).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data ingestion output schema in tests/test_ingest.py"

# Launch models for User Story 1 together:
Task: "Implement code/ingest.py: Fetch UV-Vis data..."
Task: "Implement code/validate_data.py: Data Validity Gate..."
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
- **Critical Constraint**: All model training and data processing MUST run on CPU-only (2 vCPU, 7GB RAM) within 6 hours. No GPU, no 8-bit/4-bit quantization, no large models.
- **Data Integrity**: Real data must be streamed or sampled explicitly; synthetic fallbacks are strictly prohibited.
- **Fail Loud**: If real data fetch fails, raise an exception. Do NOT fall back to synthetic data.
- **Data Hygiene**: Raw data in `data/raw/`, processed data in `data/processed/`.