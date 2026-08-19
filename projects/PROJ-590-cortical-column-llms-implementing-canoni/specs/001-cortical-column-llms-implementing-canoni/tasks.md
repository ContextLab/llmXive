# Tasks: Cortical Column LLMs: Implementing Canonical Microcircuits for Universal Computation

**Input**: Design documents from `/specs/001-cortical-column-llms/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

**Purpose**: Project initialization and basic structure. Tasks are split into atomic steps for deterministic execution.

- [ ] T001a [P] Create directory `src/`.
- [ ] T001b [P] Create directories `models`, `data`, `training`, `experiments`, `utils` inside `src/`.
- [ ] T001c [P] Create directories `tests/unit`, `tests/integration`, `scripts`, `data/results`, `data/logs`, `data/configs`, `state/`. **CRITICAL**: Ensure `state/*.yaml` is NOT in `.gitignore` to ensure it IS tracked and checksummed as required by Constitution Principle V (Versioning Discipline).
- [ ] T002 [P] Create `__init__.py` in every `src/` and `tests/` directory.
- [ ] T003 [P] Create `.gitignore` file excluding `data/`, `__pycache__`, `*.pyc`, `*.log`. **CRITICAL**: Explicitly include `!data/configs/`, `!data/results/`, `!data/logs/`, `!state/`, and `state/` to ensure experiment metadata, results, logs, and versioning artifacts are tracked for Constitution Principle IV and V.
- [ ] T004 [P] Verify Setup: Run a script to confirm all directories from T001 exist and `state/template.yaml` is present. **Output**: Exit 0 if all present, exit 1 otherwise. **CRITICAL**: This task must pass before Phase 2 starts.
- [ ] T005 Initialize Python 3.11 project with `requirements.txt` (PyTorch CPU-only, numpy, scipy, pytest, psutil).
- [ ] T006a [P] Create `ruff.toml` configuration file with strict rules for linting as per project standards.
- [ ] T006b [P] Create `pyproject.toml` or `black.toml` configuration for formatting as per project standards.
- [ ] T007 [P] Configure `tests/conftest.py` with `pytest-timeout` settings for unit tests and resource monitoring hooks.
- [ ] T007b [P] Implement `tests/conftest.py` hooks using `psutil` to assert RSS memory < 7GB and core pinning (via `os.sched_getaffinity` or `taskset` integration) during test execution. This satisfies FR-004 and SC-005 by enforcing resource constraints directly in the Python test harness.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**Note**: T009 (Baseline) and T010 (Homeostasis utilities) are now in phase 4.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008a [P] Implement `src/data/benchmarks.py` for synthetic function generation (Lorenz attractor, Fourier series, polynomial surfaces) with deterministic seeding. **CRITICAL**: Implement distinct generator functions `generate_training_data()` (Lorenz) and `generate_test_data()` (Polynomials/Fourier) to ensure independent distributions for US1 and prevent data leakage.
- [ ] T008b [P] Implement `src/data/benchmarks.py::verify_independence` function. **Signature**: `def verify_independence(train_data: np.ndarray, test_data: np.ndarray) -> bool`. **Logic**: Perform Kolmogorov-Smirnov (KS) test. **Requirement**: If `p_value < 0.05`, distributions are statistically different (independent). If `p_value >= 0.05`, log the p-value and proceed without raising an exception. **Output**: Return `True` if distributions are distinct; otherwise return false.. **CRITICAL**: This function satisfies Constitution Principle VII and FR-006 by ensuring the test set is from a different distribution.
- [ ] T008c [P] Implement task to generate independent test data for ablation/generalization metrics.
- [ ] T010a [P] Implement core homeostatic scaling logic in `src/training/homeostasis.py`: define `scale_weights(model, target_ratio, decay_rate)` function that applies synaptic scaling to maintain E/I ratio. Use formula: `scale_factor = target_activity / current_activity`. Returns a dict of applied scaling factors. Explicitly derive `target_activity` from the E/I ratio constraint.
- [ ] T010b [P] Implement gradient norm logging in `src/training/homeostasis.py`: define `log_gradient_norms(model, step)` function that computes and appends gradient norms to `data/logs/gradient_norms.json` for SC-002 verification.
- [ ] T010c [P] Implement dynamic E/I ratio enforcement mechanism in `src/training/homeostasis.py`: enforce the ratio *per batch* during training, not per epoch.

---

## Phase 3: User Story 1 - Baseline Transformer Training and Validation (Priority: P1) 🎯 MVP

**Goal**: Establish a computationally universal baseline using a standard Transformer on synthetic tasks to serve as the control.

**Independent Test**: Execute training on held-out synthetic functions (Lorenz, Fourier) and verify MAE < 0.05 within 6 hours on 4 CPU cores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T011 [US1] Integration test for baseline training pipeline in `tests/integration/test_baseline_training.py`.
- [ ] T011b [US1] Integration test in `tests/integration/test_baseline_training.py` that explicitly runs the baseline model with `log_gradient_norms` enabled to populate `data/logs/gradient_norms.json` for SC-002 verification.
- [ ] T031 [US1] Statistical test for gradient stability in `tests/integration/test_gradient_stability.py`.

### Implementation for User Story 1

- [ ] T009a [US1] Implement `src/models/baseline_transformer.py` (standard Transformer MLP/Attention layers).
- [ ] T012b_impl [US1] Implement CPU-optimized training loop, gradient clipping, resource monitoring and logging of MAE.
- [ ] T013 [US1] Create `scripts/run_baseline.sh`.
- [ ] T013b [US1] Update `scripts/run_baseline.sh` to explicitly call data generation functions for training and testing.
- [ ] T013c [US1] Implement `src/experiments/baseline_runner.py` to manage experiment configuration and logging.
- [ ] T015 [US1] Implement `src/experiments/baseline_runner.py::run_and_record_metrics`.

---

## Phase 4: User Story 2 - Microcircuit Module Implementation and Integration (Priority: P1)

**Goal**: Implement a parameterized "Cortical Column" module mimicking laminar structure with local E/I loops and homeostatic scaling.

- [ ] T009d [US2] Implement `src/models/microcircuit.py` layer definitions by creating classes `L23Layer`, `L4Layer`, `L5Layer`, `L6Layer`.
- [ ] T009f [US2] Implement `src/models/microcircuit.py` connectivity mask generation logic to enforce laminar topology.
- [ ] T010c (see Phase 2) -- Reused from Foundational phase.

---

## Phase 5: User Story 3 - Ablation and Scaling Law Analysis (Priority: P2)

**Goal**: Run systematic ablation study and scaling analysis to quantify "cost of biological plausibility".

- [ ] T025a [US3] Implement `src/experiments/ablation.py::generate_ablation_configs`
- [ ] T025b [US3] Implement `src/experiments/ablation.py::run_ablation_study`.
- [ ] T026 [US3] Implement `src/experiments/scaling.py`.
- [ ] T027 [US3] Implement `src/utils/statistics.py`.
- [ ] T028 [US3] Create `src/utils/report_generator.py::generate_cost_curve_data`

---

## Phase 6: Reviewer Response - Scaling Laws (Geoffrey West)

**Goal**: Address Geoffrey West's concern regarding scaling exponents and metabolic cost by explicitly measuring and reporting the scaling law.

- [ ] T049 [US3] Extend `src/experiments/scaling.py`
- [ ] T050 [US3] Update `src/utils/scaling_analyzer.py`.

---

## Phase 7: Reviewer Response - Structure Verification (Constitution Principle VI)

**Goal**: Address Constitution Principle VI by verifying the implemented microcircuit strictly adheres to the fixed canonical topology.

- [ ] T069 [US2] Implement `src/utils/structure_verifier.py::verify_canonical_topology`
- [ ] T069b [US2] Verify that homeostatic scaling is active and functioning as the default configuration.
