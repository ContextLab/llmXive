---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Molecular Properties from Vibrational Spectra with Deep Learning

**Input**: Design documents from `/specs/001-predicting-molecular-properties-from-vib/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `specs/`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (torch, scikit-learn, pandas, numpy, scipy, datasets, tensorboard)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/utils/timeout_wrapper.py` to enforce a strict runtime limit (FR-006) and **log the specific cause of termination** (timeout vs. NaN vs. error) to the state file and logs.
- [X] T005 Create `code/utils/update_state.py` to compute SHA-256 hashes and update `state/...yaml` (Principle V)
- [X] T006 Create `code/utils/seed_utils.py` to pin random seeds for reproducibility (Principle I)
- [ ] T007 Setup `data/` directory structure (`raw/`, `preprocessed/`, `external/`)
- [ ] T008 Create `contracts/` schema files (`dataset.schema.yaml`, `model_output.schema.yaml`, `evaluation_results.schema.yaml`)
- [X] T009 Create `code/main.py` as a CLI skeleton with argparse subcommands for each phase (download, preprocess, train, evaluate, validate) to ensure additive integration in later phases

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download QM9 and IR-spectra, align via InChIKey, and transform to normalized tensors.
**Note**: Per Spec Assumptions, data quality (DFT consistency) is assumed. No active DFT verification task is created.

**Independent Test**: The pipeline can be tested by running the data download and preprocessing script alone, verifying that the output is a single `.npz` file containing aligned spectra and property vectors, and that the file size is < 10 GB.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data alignment in `tests/test_data_alignment.py` (verifies InChIKey match)
- [X] T011 [P] [US1] Unit test for preprocessing artifacts in `tests/test_preprocessing.py` (verifies grid fidelity, smoothing, normalization)
- [X] T012 [P] [US1] Unit test for error handling in `tests/test_data_errors.py` (verifies fast fail on corrupted data/missing properties)

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/download.py` to fetch QM9 and IR-spectra from verified URLs (datasets.load_dataset or direct URL)
- [X] T019 [P] [US1] Perform Coverage Audit (KS-test) comparing property distributions between **raw QM9 (from T013)** and the **aligned subset (from T014)** to detect selection bias. **CRITICAL: This MUST run BEFORE T014 (Filtering) and can run in parallel with T013.** Log warning if p < 0.05; Write coverage audit results to `results/coverage_audit.json` with schema: `{p_value, statistic, method, sample_size}`. **Depends on T013.**
- [X] T014 [US1] Implement `code/data/preprocess.py` to perform the full pipeline:
  1. **Alignment**: Inner join on `InChIKey` and log discarded count.
  2. **Validation**: **Assert** that the final aligned molecule count is **≥ 129,000**. If not, raise a hard error and exit (FR-001).
  3. **Interpolation**: Interpolate spectra to a fixed wavenumber grid covering **400–4000 cm⁻¹** with **1 cm⁻¹ spacing** (FR-002, Constitution Principle VI).
  4. **Smoothing**: Apply Gaussian smoothing (σ = 2 cm⁻¹).
  5. **Normalization**: Normalize to unit area.
  6. **Filtering**: Filter molecules missing dipole, polarizability, or HOMO-LUMO gap; log the count of discarded samples.
  7. **Save**: Write final aligned `.npz` to `data/preprocessed/`.
  8. **Logging**: Write structured logs for download size, mismatch count, and final counts to `logs/data_ingestion.log`. **Depends on T013.**

- [X] T016 [US1] Add `code/main.py` subcommand logic to orchestrate download -> coverage audit -> preprocess -> save `.npz`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - 1-D CNN Model Training and Validation (Priority: P2)

**Goal**: Train a CPU-only 1-D CNN with 3 regression heads using early stopping.
**Note**: This phase consumes the pre-aligned `.npz` file from Phase 3. No re-filtering or re-alignment occurs.

**Independent Test**: The training script can be tested by running it on a subset of the data to verify that the loss decreases, the checkpoint is saved, and the process completes within a reasonable time on a CPU-only runner.

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for model architecture in `tests/test_model.py` (verifies 3 heads, kernel sizes 9/7/5, no CUDA ops)
- [X] T021 [P] [US2] Unit test for training loop in `tests/test_training.py` (verifies early stopping trigger and checkpoint save)
- [X] T020 [P] [US2] Integration test for NaN detection in `tests/test_training_stability.py` (verifies immediate stop on NaN loss)

### Implementation for User Story 2

- [X] T025 [US2] Implement `code/models/cnn_1d.py` with exactly three convolutional blocks (kernel sizes **9, 7, and 5**; 64 filters each), ReLU, max pooling, and three separate regression heads (dipole, polarizability, HOMO-LUMO).
- [X] T026 [US2] Implement `code/models/trainer.py` with:
 - Adam optimizer (lr=1e-3)
 - Early stopping with patience=10 monitoring 'val_loss' (weighted sum of 3 heads)
 - CPU-only execution (explicitly disable CUDA, standard float precision)
 - TensorBoard logging to 'runs/training/'
- [X] T023 [US2] Integrate `code/models/trainer.py` with `code/main.py` subcommand to load preprocessed `.npz`, split data, train, and save best checkpoint (`model_best.pt`). **Depends on T014.**
- [X] T024 [US2] Integrate `code/main.py` timeout enforcement using `code/utils/timeout_wrapper.py` during training, ensuring the **cause of termination** (timeout vs. error) is logged to the state file and logs. **Depends on T004 and T023.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Evaluation and Significance Testing (Priority: P3)

**Goal**: Evaluate model on test set (MAE, R²) and perform paired-sample t-tests for systematic bias (Primary) and TOST/Hotelling's (Secondary/Exploratory).

**Independent Test**: The evaluation script can be tested by running it on a saved model checkpoint and a test set, verifying that it outputs a JSON report with MAE, R², and p-values.

### Tests for User Story 3

- [X] T027 [P] [US3] Unit test for metrics calculation in `tests/test_evaluation.py` (verifies MAE, R² formulas)
- [X] T028 [P] [US3] Unit test for statistical tests in `tests/test_statistics.py` (verifies t-test, TOST, and Hotelling's T² implementation)

### Implementation for User Story 3

- [X] T029 [US3] Implement `code/evaluation/metrics.py` to compute MAE and R² for each of the target properties
- [X] T032 [US3] Implement `code/evaluation/metrics.py` to perform paired-sample t-tests (Primary Validation per SC-003, null hypothesis: mean error = 0); explicitly verify if **p-value < 0.01** for systematic bias. **CRITICAL: If p-value >= 0.01, the script MUST raise an assertion error or exit with a failure status.** Record the actual p-value, mean error, and pass/fail status in `results/evaluation_metrics.json`.
- [X] T033 [US3] Implement `code/evaluation/metrics.py` to perform TOST (equivalence) and Hotelling's T² tests (Secondary/Exploratory per Plan Phase 3)
- [X] T030a [US3] Implement `code/evaluation/evaluate.py` to load `model_best.pt` and test set, run inference, and save predictions to `results/predictions_test.npz`. **Depends on T023 and T014.**
- [X] T030b [US3] Implement `code/evaluation/evaluate.py` to generate `results/evaluation_metrics.json` with schema {dipole: {mae, r2, p_value, bias_pass_fail},...}
- [X] T031 [US3] Integrate `code/evaluation/evaluate.py` with `code/main.py` subcommand to run after training
- [X] T034 [US3] Add logic to `code/utils/update_state.py` to hash `results/evaluation_metrics.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Independent Validation (Priority: P4)

**Goal**: Validate model generalizability on an independent dataset (experimental or different DFT method).
**Note**: Per FR-007, if external data is missing, the task MUST fail with a clear error. Synthetic noise is NOT a valid substitute for real data.

**Independent Test**: The validation script can be tested by running it on an external dataset file, verifying that it outputs a separate JSON report with MAE and R² distinct from the training/test set results.

### Tests for User Story 4

- [X] T035 [P] [US4] Integration test for independent validation in `tests/test_independent_validation.py` (verifies separate metric reporting)

### Implementation for User Story 4

- [X] T038a [US4] Implement `code/evaluation/validate.py` (Real Data Path):
 - **Check Existence**: Verify the existence of the external validation dataset at `data/external/val.csv` or `data/external/val.h5`.
 - **Fail Fast**: If the file does not exist, **raise a clear error** and exit immediately. Do NOT proceed to any simulation or fallback.
 - **Evaluate**: If the file exists, load the external validation dataset (experimental or different DFT method).
 - **Compute Metrics**: Compute MAE/R² and compare against test set (tolerance ≤ 20% increase).
 - **Output**: Generate `results/validation_results.json` with separate metrics.
 - **Depends on T023.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `specs/001-predicting-molecular-properties-from-vib/quickstart.md`: Add a section on data download commands, preprocessing steps, and a table of hyperparameters (lr, patience, kernel sizes). **CRITICAL: This task MUST verify the generation of all required artifacts: `logs/data_ingestion.log`, `results/profile_report.txt`, `results/runtime_verification.json`, and `results/evaluation_metrics.json` as part of the final deliverable checklist.**
- [ ] T043 [P] Run static analysis (`ruff check --fix`) on `code/` and fix all reported issues. **Explicitly run `ruff check --fix` and ensure exit code 0.**
- [X] T044 [P] Profile `code/main.py` with `cProfile`, identify top memory bottlenecks, and optimize dataset loading to reduce peak RAM usage to ≤ 7 GB RAM; generate `results/profile_report.txt` and `results/memory_log.txt`
- [ ] T046 [P] Run `tests/` suite to verify all acceptance scenarios. **Explicitly run `pytest -v --cov` and ensure exit code 0.**
- [X] T045 [P] Run `code/main.py` end-to-end to verify the established time limit. **Mechanism**: Measure wall-clock time, compare against the **6 hours** threshold defined in the spec/plan, and write `results/runtime_verification.json` with the result (pass/fail) and the specific duration measured.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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
# Launch all tests for User Story 1 together:
Task: "Contract test for data alignment in tests/test_data_alignment.py"
Task: "Unit test for preprocessing artifacts in tests/test_preprocessing.py"
Task: "Unit test for error handling in tests/test_data_errors.py"

# Launch implementation tasks in parallel where possible:
Task: "Implement code/data/download.py"
Task: "Perform Coverage Audit (T019)" (Depends on T013, runs parallel to T013)
Task: "Implement code/data/preprocess.py (Full pipeline)" (Depends on T013)
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
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

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
- **CPU Constraint**: All model training tasks MUST strictly avoid CUDA/8-bit quantization.
- **Data Constraint**: All data tasks MUST use real, verified URLs or package fetchers. No synthetic/fake data.
- **Validation Constraint**: Independent validation (US4) requires a real external dataset. **No synthetic fallback is permitted.** If data is missing, the pipeline fails.