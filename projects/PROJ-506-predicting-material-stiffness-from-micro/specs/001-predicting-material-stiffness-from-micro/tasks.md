---
description: "Task list for feature implementation"
---

# Tasks: Predicting Material Stiffness from Microstructure Images Using Convolutional Neural Networks

**Input**: Design documents from `/specs/001-predict-stiffness-cnn/`
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

## Phase 0: Governance & Constitution Amendment (Prerequisite)

**Purpose**: Align project governance and specification text with scientific requirements before code execution.
**⚠️ CRITICAL**: No data generation or training can begin until this phase is complete.

- [X] T001 [P] Draft `docs/constitution_amendment_proposal.md` justifying the shift from analytical to FFT-based homogenization (Plan Task 0.1).
- [ ] T002a [P] **Amend Constitution**: Update `constitution.md` Principle VI to explicitly permit FFT-based numerical homogenization as the ground-truth method. This task must be completed and committed before T002c can run.
- [X] T002c [P] **Create Verification Script**: Create `code/utils/verify_constitution.py` to assert that Principle VI has been updated. Depends on T002a (to have content to verify) but must exist before T002b runs.
- [X] T002b [P] **Run Verification Script**: Execute `python code/utils/verify_constitution.py` to assert that Principle VI has been updated. This task depends on T002a and T002c.
- [ ] T002 [P] **Gate Check**: Verify that `constitution.md` Principle VI is updated. If T002b fails, this task blocks progress. (Depends on T002b). <!-- FAILED: unspecified -->
- [X] T003 [P] Update `state/projects/PROJ-506-predicting-material-stiffness-from-micro.yaml` `artifact_hashes` and `updated_at` to record the governance change (Plan Task 0.3).
- [ ] T004a [P] **Amend Spec Resolution**: Update `spec.md` FR-001 and US-1 Acceptance Scenario 1 to explicitly state "128x128 pixels" if not already present. This task must be completed before T004c.
- [X] T004c [P] **Create Verification Script**: Create `code/utils/verify_spec.py` to assert that FR-001 and US-1 state "128x128 pixels". Depends on T004a.
- [X] T004 [P] **Verify Spec Resolution**: Execute `python code/utils/verify_spec.py` to assert that FR-001 and US-1 explicitly state "128x128 pixels". If T004c fails, this task blocks progress. (Depends on T004a, T004c).
- [ ] T005a [P] **Amend Spec/Plan**: Update `spec.md` and `plan.md` to explicitly reflect the shift to "One-way ANOVA and Tukey HSD" if not already present. This task must be completed before T005c.
- [X] T005c [P] **Create Verification Script**: Create `code/utils/verify_spec_anova.py` to assert that FR-007, SC-004, and US-3 explicitly state "One-way ANOVA and Tukey HSD". Depends on T005a.
- [X] T005 [P] **Gate Check**: Verify that `spec.md` FR-007, SC-004, and US-3 Acceptance Scenario 2 explicitly state "One-way ANOVA and Tukey HSD". If T005c fails, this task blocks progress. (Depends on T005a, T005c).

**Gate**: Proceed to Phase 1 only after T001-T005a are committed and T002/T005 are marked [X].

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T006a [P] Create project directories. Execute: `mkdir -p code/{data_generation,training,evaluation,utils} data/{raw,processed} tests/{unit,contract,integration} specs/001-predict-stiffness-cnn/contracts`. Verify the directory tree exists using `tree code data tests specs` and assert exit code 0.
- [X] T006b [P] Create `__init__.py` files. Execute: `touch code/__init__.py code/data_generation/__init__.py code/training/__init__.py code/evaluation/__init__.py code/utils/__init__.py tests/__init__.py tests/unit/__init__.py tests/contract/__init__.py tests/integration/__init__.py`. Verify all files exist.
- [X] T006c [P] Create placeholder files. Execute: `touch code/main.py code/data_generation/generate_microstructures.py code/data_generation/compute_stiffness.py code/training/model.py code/training/train.py code/evaluation/stats_utils.py code/evaluation/evaluate.py docs/constitution_amendment_proposal.md`. Verify all files exist.
- [X] T007 Initialize Python + project. Create `requirements.txt` with the following exact content, or reference a template file if versions need resolution:
 ```text
 torch==2.0.0+cpu
 scikit-image==0.21.0
 scipy==1.11.0
 numpy==1.24.0
 pandas==2.0.0
 pytest==7.3.0
 scikit-learn==1.2.0
 pyfftw==0.13.1
 ```
- [X] T008 [P] Configure linting and formatting. Create `pyproject.toml` with `ruff` and `black` configuration. Enable rules for `E`, `F`, `W`, `I`, and `N`. Execute `ruff check.` and `black --check.` to verify configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Implement core FFT-based homogenization solver in `code/utils/fft_homogenization.py` (CPU-optimized, no CUDA). Note: Constitution Principle VI has been amended to permit this method (T002a).
- [X] T010 [P] Implement utility metrics functions (`MAE`, `MSE`, `R2`) in `code/utils/metrics.py`
- [X] T011 Setup k-fold cross-validation utilities in `code/training/kfold_utils.py`
- [ ] T012 Create data schema validation contracts in `specs/001-predict-stiffness-cnn/contracts/dataset.schema.yaml`. File format: YAML. Required fields: `image_path: string`, `stiffness_tensor: float[]`, `inclusion_density: float`, `topology_type: string`, `shape_factor: float`, `connectivity: float`, `seed: integer`.
- [ ] T013 Create model output schema contracts in `specs/001-predict-stiffness-cnn/contracts/model-output.schema.yaml`. File format: YAML. Required fields: `model_version: string`, `prediction: float[]`, `error: float`, `density_bin: string`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Data Generation and Ground Truth Calculation (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic microstructure images with known ground truth stiffness (US-1) with varying void/inclusion densities and compute their effective elastic stiffness tensors using FFT-based numerical homogenization.

**Independent Test**: Output directory contains ≥ 2,000 image files and a metadata file with stiffness tensors within Voigt-Reuss-Hill bounds.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T014 [P] [US1] Unit test for microstructure generation logic in `tests/unit/test_generation.py`
- [X] T015 [P] [US1] Unit test for FFT homogenization convergence in `tests/unit/test_homogenization.py`
- [X] T016 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (depends on T012)

### Implementation for User Story 1

- [X] T017 [US1] Implement stratified microstructure generator in `code/data_generation/generate_microstructures.py` (FR-001, uses `scikit-image`, ensures density-topology decoupling). Output: PNG files in `data/raw/` named `micro_{seed}.png` (128x128 pixels, as per amended FR-001 in T004). **Depends on T012**.
- [ ] T017b [US1] **Calculate Topological Metrics**: Extend T017 to calculate `shape_factor` and `connectivity` for each generated microstructure and include them in the metadata. (Depends on T017).
- [X] T018 [US1] Implement stiffness tensor calculator in `code/data_generation/compute_stiffness.py` (FR-002, calls FFT solver, outputs to `data/raw/`). **Depends on T012**.
- [X] T019 [US1] Add validation logic to check physical plausibility of generated tensors (Voigt-Reuss-Hill bounds) and schema conformity (depends on T012, T009, T017, T018). Note: VRH used ONLY for filtering invalid runs; ground truth is the FFT value. Explicitly validate that FFT results fall within VRH bounds; if not, flag and exclude. **CRITICAL**: Log the specific reason for exclusion (e.g., "Solver Convergence Failure" or "Unphysical Microstructure") to `data/processed/validation_log.csv` instead of silent exclusion.
- [X] T020 [US1] Create orchestration script `code/main.py` to run generation pipeline end-to-end. CLI args: `--seed`, `--n_samples`. Sequence: generate -> compute -> validate. Exit codes: 0=success, 1=fail. (depends on T017, T018, T019).
- [ ] T021 [US1] Log derivation metadata (seeds, parameters, density values, shape_factor, connectivity) to `data/processed/derivation_log.json` (depends on T020).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Optimized CNN Training and Validation (Priority: P2)

**Goal**: Train a shallow Convolutional Neural Network on the generated dataset using PyTorch in CPU-only mode, ensuring completion within 6 hours.

**Independent Test**: Training completes within 6 hours on 2-core CPU, saves model artifact, and reports MSE/R2.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for CNN architecture definition in `tests/unit/test_model.py`
- [X] T024 [P] [US2] Contract test for model output schema in `tests/contract/test_output_schema.py` (depends on T013). **Note**: This is a TDD task; write this file first, ensure it fails, then implement T025/T026 to pass.

### Implementation for User Story 2

- [X] T025 [P] [US2] Implement shallow CNN architecture (Several convolutional layers, ReLU, global avg pooling) in `code/training/model.py` (FR-003)
- [X] T026 [US2] Implement training loop with Adam optimizer, batch size 32, and **A sufficient number of epochs will be employed to ensure model convergence, with the exact count determined during the implementation phase.** (or early stopping) in `code/training/train.py` (FR-004)
- [ ] T027 [US2] Integrate k-fold cross-validation logic into training script (FR-005)
- [X] T028 [US2] Implement data streaming/batching in `code/training/data_loader.py`. Class `MicrostructureDataLoader` with method `__iter__` yielding batches of a size appropriate to respect the available RAM limit.
- [ ] T029 [US2] Add checkpointing to save model weights to `code/models/` on completion
- [ ] T030 [US2] Implement evaluation on held-out test set to compute MAE, MSE, R2 (FR-006)
- [X] T031 [US3] **Stratified K-Fold Implementation**: Implement k-fold cross-validation stratified by `inclusion_density` and `topology_type` (as defined in T012) and `shape_factor`/`connectivity` bins (as calculated in T017b) in `code/training/train.py`. (FR-005, depends on T011, T029, T017b). **Note**: This task is placed in Phase 5 (US-3) to ensure independence, but depends on the model artifact (T029) and utilities (T011), not the US-2 implementation details (T027).
- [ ] T032 [US2] **Stability Reporting**: Calculate and report the variance/standard deviation of R-squared values across the folds to satisfy SC-005. Output: Append specific numeric values to `data/processed/analysis_report.md`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generalization and Statistical Analysis (Priority: P3)

**Goal**: Evaluate model generalization across inclusion densities and perform statistical tests (One-way ANOVA per amended spec T005) on prediction errors.

**Independent Test**: Verify report shows error degradation for out-of-distribution densities, statistically significant p-values from ANOVA, and degradation rate metric.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for statistical analysis functions in `tests/unit/test_stats_utils.py`

### Implementation for User Story 3

- [ ] T034 [P] [US3] Implement One-way ANOVA and Tukey HSD functions in `code/evaluation/stats_utils.py` (Plan Methodology Update - primary verification method for FR-007, per amended spec T005).
- [ ] T035 [US3] Implement evaluation script `code/evaluation/evaluate.py` to bin data by density, compute errors, and call T034 for primary verification (FR-007).
- [ ] T036 [US3] **OOD Threshold Definition**: Calculate and explicitly report the `max_training_density` threshold derived from the training set metadata (from T021) to define the boundary for Out-of-Distribution (OOD) analysis (SC-002). Calculation: **Maximum density value** observed in the training set metadata. Report the specific numeric value used. **Note**: This threshold is configurable; if a different boundary (e.g., 95th percentile) is required by future specs, this task must be updated. Default is max.
- [ ] T037 [US3] Calculate and report quantitative 'degradation rate' metric for out-of-distribution densities (SC-002). Formula: slope of (MAE vs. density) for densities > `max_training_density` (from T036). Unit: MAE per % density. Output: Append specific numeric value to `data/processed/analysis_report.md`.
- [ ] T038a [US3] **OOD Flagging Logic (Cause)**: Implement logic to flag instances where `inclusion_density > max_training_density` (from T036) (FR-008). **Correction**: Flag based strictly on the input density value exceeding the defined OOD threshold.
- [ ] T038b [US3] **Error-Based Flagging (Symptom)**: Implement logic to flag instances where `error > 10% MAE` for diagnostic purposes only, distinct from OOD flagging. (Optional, for FR-008 context).
- [ ] T039a [US3] Generate analysis report section: Error vs Density plot (matplotlib) to `data/processed/analysis_report.md`.
- [ ] T039b [US3] Generate analysis report section: Degradation rate table (numeric values from T037) to `data/processed/analysis_report.md`.
- [ ] T039c [US3] Generate analysis report section: ANOVA/Tukey HSD table and p-values (from T034) to `data/processed/analysis_report.md`.
- [ ] T040 [US3] Add logic to detect and report out-of-distribution density failures
- [ ] T022 [US3] **Success Criterion Verification**: Compute and report the Mean Absolute Error (MAE) of the model's predictions against the FFT-based numerical ground truth on a held-out test set to verify the % MAE threshold (SC-001). Output: Append specific numeric value to `data/processed/analysis_report.md`. (Note: This task verifies the MODEL's performance, not the dataset generation against VRH. Depends on T029, T020).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041a [P] Update `README.md` with CLI usage, installation instructions, and project overview.
- [ ] T041b [P] Generate API docs for `code/utils/` and `code/data_generation/` using `sphinx` or `pdoc`.
- [ ] T041c [P] Update `docs/research.md` with methodology summary and key findings.
- [ ] T042 Code cleanup and refactoring of data loading utilities
- [ ] T043 Performance optimization of FFT solver for CPU cache efficiency
- [ ] T044 [P] Additional unit tests for edge cases (extreme void density, solver convergence) in `tests/unit/`
- [ ] T045 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T046 Verify full pipeline runtime is ≤ 6 hours on simulated free-tier constraints.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Governance)**: No dependencies - can start immediately. **BLOCKS** all subsequent phases.
- **Setup (Phase 1)**: Depends on Phase 0 completion.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model training

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
Task: "Unit test for microstructure generation logic in tests/unit/test_generation.py"
Task: "Unit test for FFT homogenization convergence in tests/unit/test_homogenization.py"

# Launch implementation tasks for User Story 1 together:
Task: "Implement stratified microstructure generator in code/data_generation/generate_microstructures.py"
Task: "Implement stiffness tensor calculator in code/data_generation/compute_stiffness.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Governance & Constitution Amendment
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
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