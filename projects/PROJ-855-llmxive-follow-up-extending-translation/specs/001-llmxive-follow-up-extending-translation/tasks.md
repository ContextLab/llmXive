# Tasks: llmXive follow-up: extending "Translation as a Bridging Action"

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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-855-llmxive-follow-up-extending-translation/`) **including the `contracts/` directory**
- [ ] T001b Generate `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml` based on `data-model.md` definitions to ensure contract tests have valid schemas to validate against
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils/data_utils.py` for schema validation and checksum verification
- [ ] T005a [P] Implement `code/utils/physics_metrics.py` for tipping angle and slippage distance calculations, **including loading configurable thresholds from `config.yaml`**
- [ ] T005b Create `code/config.yaml` with default thresholds (tipping_angle=15.0, slippage=0.02) and structure for sensitivity analysis parameters
- [ ] T006 Create `data/` directory structure (`raw/`, `processed/`) and initialize `data/checksums.json`
- [ ] T007 [P] Implement `tests/unit/test_labeling.py` to validate physics metric logic
- [ ] T008 [P] Implement `tests/contract/test_schemas.py` to validate output against `specs/001-gene-regulation/contracts/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Data Generation & Labeling (Priority: P1) 🎯 MVP

**Goal**: Generate ≥5,000 bi-manual manipulation episodes using PyBullet on CPU, labeling them with stability outcomes based on physics metrics, ensuring strict exclusion of rotation/force data.

**Independent Test**: The system can be tested by running `code/generate_data.py` and verifying that the output CSV/Parquet files contain exactly the required columns (translation vectors, initial object bounds) and a binary label column, with no rotation or force data present.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py`
- [ ] T010 [P] [US1] Unit test for stability labeling logic (tipping/slippage thresholds) in `tests/unit/test_labeling_logic.py`

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/generate_data.py` with PyBullet simulation, noise injection, and episode generation loop
- [ ] T012 [US1] Implement logic in `code/generate_data.py` to record ONLY relative wrist translation vectors and initial object bounding box coordinates
- [ ] T013 [US1] Implement logic in `code/generate_data.py` to discard rotation quaternions, joint torques, and force sensor readings explicitly
- [ ] T014 [US1] Implement labeling logic in `code/generate_data.py` to assign binary stability (1/0) based on **thresholds loaded from `config.yaml`** (tipping angle ≥ 15° or slippage ≥ 0.02m)
- [ ] T015 [US1] Implement error handling in `code/generate_data.py` to catch numerical instabilities, discard incomplete episodes, and generate replacements to ensure ≥ 5,000 valid rows
- [ ] T016 [US1] Save generated dataset to `data/raw/synthetic_episodes.parquet` and update `data/checksums.json`
- [ ] T017 [US1] **Validate Raw Data**: Add validation step in `code/generate_data.py` to verify no forbidden columns exist **in the just-saved raw file** (enforcing FR-001). **This task must run immediately after T016**.
- [ ] T016b [US1] **Derive** model-ready data from `data/raw/synthetic_episodes.parquet` to `data/processed/train.parquet` and `data/processed/test.parquet`; **ensure raw data remains immutable by reading only** and writing new files to `data/processed/`
- [ ] T016c [US1] **Implement geometry-disjoint split**: In `code/generate_data.py` (or a helper script), split the raw data into train/test sets **based on unique object geometry IDs** to ensure the test set contains ONLY geometries not present in the training set. Save these as `data/processed/train.parquet` and `data/processed/test.parquet`.
- [ ] T016d [US1] **Assert dataset validity**: Add a validation step to `code/generate_data.py` that asserts the total row count of `train.parquet` + `test.parquet` is ≥ 5,000 AND explicitly asserts that `test.parquet` contains ≥ 1,000 rows to ensure statistical power for US-3. Fail the script if these thresholds are not met.
- [ ] T018 [US1] **Re-labeling for Sensitivity**: Add a function to `code/generate_data.py` that accepts custom thresholds (from `config.yaml` sweep), re-computes labels on the **raw** `synthetic_episodes.parquet`, and **re-executes the geometry-disjoint split logic (T016c)** to produce new processed splits for sensitivity analysis.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight Sequence Model Training (Priority: P2)

**Goal**: Train a <10M parameter Transformer encoder on the generated dataset using only translation trajectories, ensuring execution within 6 hours on a 2-core CPU with 7GB RAM.

**Independent Test**: The system can be tested by initiating the training job on a standard GitHub Actions runner (2 CPU, 7GB RAM) and verifying that the job completes without OOM errors, GPU allocation failures, or exceeding the 6-hour time limit.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for model architecture parameter count in `tests/unit/test_model_params.py`
- [ ] T020 [P] [US2] Integration test for CPU-only training loop in `tests/integration/test_cpu_training.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/models/transformer.py` with a 4-layer Transformer encoder constrained to <10M parameters
- [ ] T022 [US2] Implement `code/train_model.py` to load data from `data/processed/` (specifically `train.parquet`) and configure CPU-only training (no CUDA, no bitsandbytes)
- [ ] T023 [US2] Implement training loop in `code/train_model.py` using binary cross-entropy loss, default floating-point precision, **integrated timeout handling**, and **instrument `psutil` to log peak RAM usage to stdout with prefix `[RAM-PEAK-MB]: <value>`** to satisfy SC-002 verification.
- [ ] T024 [US2] Save trained model weights to `data/processed/trained_model.pt` and log parameter count
- [ ] T025 [US2] Verify model summary output confirms < 10,000,000 parameters before saving
- [ ] T027b [US2] **Train Geometry-Only Baseline**: Implement a lightweight model (Logistic Regression or simple MLP) in `code/train_baseline.py` that uses **only** the `initial_object_bounds` feature to predict stability; save to `data/processed/baseline_model.pt`. **Depends on T016b/T016c (processed data)**.
- [ ] T027c [US2] **Train Shuffled-Translation Control**: Implement a training script `code/train_shuffled_control.py` that loads `train.parquet`, **randomly shuffles the translation trajectory sequences** to break temporal correlation while preserving marginal distributions, and trains a model on this data; save to `data/processed/shuffled_control_model.pt`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently, and all baseline models are ready for evaluation.

---

## Phase 5: User Story 3 - Statistical Validation & Baseline Comparison (Priority: P3)

**Goal**: Statistically validate the translation-only model against a geometry-only baseline and a shuffled-translation control using McNemar's test, ensuring ≥ 5% accuracy improvement on novel geometries and reporting results associatively.

**Independent Test**: The system can be tested by running the evaluation script on the held-out test set and verifying the output includes the McNemar's test p-value, the accuracy of all models, and the calculated accuracy difference.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for McNemar's test implementation in `tests/unit/test_mcnemar.py`
- [ ] T027 [P] [US3] Contract test for `metrics_report.json` schema in `tests/contract/test_metrics_report.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/evaluate.py` to load the trained Transformer model (`trained_model.pt`), the geometry-only baseline (`baseline_model.pt`), and the shuffled-translation control (`shuffled_control_model.pt`)
- [ ] T029 [US3] Implement prediction logic in `code/evaluate.py` for all three models on the held-out test set (`data/processed/test.parquet` which contains novel geometries)
- [ ] T030 [US3] Implement McNemar's test in `code/evaluate.py` to compare paired predictions (Model vs Geometry Baseline) and calculate p-value
- [ ] T031 [US3] Implement McNemar's test in `code/evaluate.py` to compare paired predictions (Model vs Shuffled Control) and calculate p-value
- [ ] T032 [US3] Implement accuracy calculation in `code/evaluate.py` to verify ≥ 5% absolute improvement over both baselines
- [ ] T033 [US3] Implement sensitivity analysis in `code/evaluate.py` to **call the re-labeling function from T018** (which sweeps thresholds ±5% on raw data and **re-runs the geometry-disjoint split logic T016c**) to compute metrics for each sweep and report accuracy variance.
- [ ] T034 [US3] Generate `data/metrics_report.json` containing accuracy, p-values, confusion matrix, and explicit associational framing (no causal claims)
- [ ] T035 [US3] Implement validation in `code/evaluate.py` to ensure test set geometries were not seen during training (verify against geometry IDs)
- [ ] T036 [US3] Add reporting logic to flag ambiguous signals (identical translation for success/failure) and report confusion matrix for this subset

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` and `README.md`
- [ ] T038 Code cleanup and refactoring across `code/`
- [ ] T039 Performance optimization to ensure total pipeline < 6 hours
- [ ] T040 [P] Additional unit tests for edge cases (tunneling, ambiguous signals) in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T016b/T016c (data processed)** from US1. **Includes T027b and T027c (Baselines)**.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on models from US2 (T025, T027b, T027c)**.
  - **CRITICAL**: Phase 5 tasks (T028+) **MUST WAIT** for the completion of T025, T027b, and T027c.
  - **Sensitivity Analysis (T033)**: **Depends explicitly on T011 (Raw Generation)** and **T016c (Geometry Split)** to ensure it re-runs the split logic on re-labeled data.

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
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Unit test for stability labeling logic in tests/unit/test_labeling_logic.py"

# Launch implementation tasks for User Story 1 together:
Task: "Implement code/generate_data.py with PyBullet simulation"
Task: "Implement logic to discard rotation/force data"
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
   - Developer A: User Story 1 (Data Generation)
   - Developer B: User Story 2 (Model Training + Baselines) - *Can start once US1 data is processed (T016c)*
   - Developer C: User Story 3 (Evaluation) - *Can start once US2 models (Main, Baseline, Control) are trained*
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
- **CRITICAL**: All tasks MUST run on CPU-only, multi-core, sufficient RAM environment. No GPU/CUDA imports allowed.
- **CRITICAL**: Dataset must be real (generated via simulation), not fabricated or hardcoded.
- **CRITICAL**: Data flow order must be respected: Data Gen (US1) → Process (T016c) → Train (US2) → Eval (US3).
- **CRITICAL**: Thresholds must be configurable via `config.yaml` (T005b) to support sensitivity analysis (T033).
- **CRITICAL**: Geometry-only baseline (T027b) and Shuffled-Translation Control (T027c) are mandatory implementation tasks, not optional.
- **CRITICAL**: T016c ensures novel geometries in test set; T016d ensures statistical power (≥1,000 test rows).
- **CRITICAL**: T023 logs RAM usage in `[RAM-PEAK-MB]: <value>` format for CI verification.
- **CRITICAL**: T033 re-runs T016c logic on re-labeled data to maintain geometry disjointness.
- **CRITICAL**: T016 (Save) MUST run before T017 (Validate) to ensure the file exists.
- **CRITICAL**: T027b and T027c are now in Phase 4 to ensure baselines are ready before Phase 5 evaluation.