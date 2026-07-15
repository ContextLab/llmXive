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

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` (directories: `src/models`, `src/data`, `src/training`, `src/experiments`, `tests`)
- [ ] T002 Initialize Python 3.11 project with `pyproject.toml` and `requirements.txt` (PyTorch CPU-only, numpy, scipy, pytest, psutil)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Configure `tests/conftest.py` with `pytest-timeout` settings for unit tests and resource monitoring hooks

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement `src/data/benchmarks.py` for synthetic function generation (Lorenz attractor, Fourier series, polynomial surfaces) with deterministic seeding
- [ ] T006 [P] Implement `src/models/baseline_transformer.py` (standard Transformer MLP/Attention layers)
- [~] T007a [P] Implement `src/models/microcircuit.py` layer definitions for L2/3, L4, L5, L6 as separate `nn.Module` sub-layers.
- [~] T007b [P] Implement `src/models/microcircuit.py` connectivity mask generation logic to enforce L4->L2/3 excitatory and other laminar connections.
- [~] T007c [P] Implement `src/models/microcircuit.py` E/I ratio enforcement logic (targeting a dominant excitatory component) by construction in the initialization and forward pass.
- [~] T008 Implement `src/training/homeostasis.py` for activity-dependent synaptic scaling mechanism
- [ ] T009 Implement `tests/unit/test_benchmarks.py` to verify synthetic data generation and checksums
- [ ] T010 Implement `tests/unit/test_microcircuit.py` to verify initial connectivity matrix shape and weight constraints

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Transformer Training and Validation (Priority: P1) 🎯 MVP

**Goal**: Establish a computationally universal baseline using a standard Transformer on synthetic tasks to serve as the control.

**Independent Test**: Execute training on held-out synthetic functions (Lorenz, Fourier) and verify MAE < 0.05 within 6 hours on 4 CPU cores.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test for data generation in `tests/unit/test_benchmarks.py` (verify independent test set distribution)
- [ ] T012 [P] [US1] Integration test for baseline training pipeline in `tests/integration/test_baseline_training.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `src/training/trainer.py` with CPU-optimized loop, gradient clipping (max norm), resource monitoring (psutil), and logic to calculate Mean Absolute Error (MAE). (Uses `pytest-timeout` for enforcement).
- [ ] T014 [US1] Create `scripts/run_baseline.sh` to orchestrate baseline training on Lorenz (train) and Polynomials (test), explicitly invoking `/usr/bin/time -v` to verify -hour time limit and GB RAM threshold as per FR-004.
- [ ] T015 [US1] Create `src/experiments/baseline_runner.py` to manage experiment configuration and logging.
- [ ] T016 [US1] Create `tests/integration/test_baseline_validation.py::test_baseline_degradation_measurement` that asserts the system records the MAE on the independent test set and calculates the degradation percentage relative to the training set, storing these metrics in `data/results/baseline_metrics.json` for cost curve generation (no hard pass/fail threshold on degradation).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Microcircuit Module Implementation and Integration (Priority: P1)

**Goal**: Implement a parameterized "Cortical Column" module mimicking laminar structure with local E/I loops and homeostatic scaling.

**Independent Test**: Instantiate module, verify connectivity matrix matches laminar topology, and confirm forward pass works on CPU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for connectivity matrix in `tests/unit/test_microcircuit.py` (verify L4->L2/3 excitatory, etc.)
- [ ] T018 [P] [US2] Unit test for E/I ratio enforcement in `tests/unit/test_microcircuit.py` (verify a forward/backward ratio during forward/backward)

### Implementation for User Story 2

- [ ] T019 [US2] Implement homeostatic scaling logic in `src/training/homeostasis.py` to dynamically maintain a balanced E/I ratio.
- [ ] T020 [US2] Create `src/models/hybrid_network.py` to replace standard MLP layers with `MicrocircuitModule` while maintaining parameter count parity (±1%).
- [ ] T021 [US2] Add weight clipping logic in `src/models/microcircuit.py` to enforce a normalized range during initialization.
- [ ] T022 [US2] Implement `src/experiments/microcircuit_runner.py` to train hybrid model on same synthetic tasks as baseline.
- [ ] T023 [US2] Create `tests/unit/test_hybrid_network.py::test_forward_pass_cpu` that instantiates the model and asserts no shape mismatches.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Ablation and Scaling Law Analysis (Priority: P2)

**Goal**: Run systematic ablation study and scaling analysis to quantify "cost of biological plausibility" and identify scaling exponents.

**Independent Test**: Train ablation variants (no recurrence, no inhibition) and scaling variants (multiple column configurations), compare errors and training times.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Statistical test for ablation impact in `tests/integration/test_ablation_stats.py` (t-test for p < 0.05)
- [ ] T025 [P] [US3] Scaling law regression test in `tests/integration/test_scaling_laws.py`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `src/experiments/ablation.py` to programmatically disable specific features (recurrence, inhibition) in `MicrocircuitModule`.
- [ ] T027 [US3] Implement `src/experiments/scaling.py` to vary column count (x, multiple of x) and measure performance vs. parameter count.
- [ ] T028 [US3] Implement `src/utils/statistics.py` to perform two-sample t-tests and calculate scaling exponents.
- [ ] T029 [US3] Create `src/utils/report_generator.py` to generate the "cost of biological plausibility" curve (MAE vs. biological constraint degree) and output to `data/results/cost_curve.json`.
- [ ] T030 [US3] Create `tests/integration/test_ablation_stats.py::test_ablation_verification` that consumes T031A results to verify the statistical significance (p < 0.05) and records the effect size without enforcing a specific threshold.
- [ ] T031A [US3] Implement statistical comparison logic in `src/utils/statistics.py` to compute the difference in MAE between full and ablated models and calculate p-values. Output must be a JSON object with keys: `{"full_mae": float, "ablated_mae": float, "mae_diff": float, "p_value": float, "significant": bool}`. (Producer task).
- [ ] T031B [US3] Create `tests/integration/test_ablation_stats.py::test_ablation_verification` that consumes T031A results to verify the JSON schema and data integrity. (Consumer task).
- [ ] T040 [US3] Implement `src/utils/scaling_analyzer.py` to fit a power-law model to the performance data from T027 (1x, 2x, 4x variants) and output the exponent with confidence intervals to `data/results/scaling_exponent.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Update `docs/quickstart.md` with instructions for running baseline, microcircuit, ablation, and scaling experiments
- [ ] T042 Code cleanup and refactoring of `src/models/` to ensure clear separation of concerns
- [ ] T043 [P] Add comprehensive logging for all experiment runs (seed, params, metrics, wall-time)
- [ ] T044 [P] Run `scripts/hash_artifacts.sh` to update `state/` YAML files with SHA256 hashes of data and code
- [ ] T045 Validate `plan.md` constraints (CPU time, RAM) are met in all integration tests
- [ ] T046 Final review of `research.md` to ensure all reviewer comments are addressed with data

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - Note: T007a, T007b, T007c (Microcircuit) are now in Phase 2 to ensure 'enforcement by construction' is available before US1/US2.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Reviewer Responses (Phase 6 & 7)**: DELETED - These were unapproved scope creep.
- **Polish (Final Phase)**: Depends on all desired user stories and reviewer responses being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - T016 (Test) is now part of Phase 3 to ensure testability during implementation.
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
 - T023 (Test) is now part of Phase 4 to ensure testability during implementation.
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - T030, T031A, T031B (Tests) are now part of Phase 5 to ensure testability during implementation.
- **Scaling Analysis (T040)**: Depends on T027 (Scaling Experiment) completion.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T006, T007a, T007b, T007c) can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data generation in tests/unit/test_benchmarks.py"
Task: "Integration test for baseline training pipeline in tests/integration/test_baseline_training.py"

# Launch all models for User Story 1 together:
Task: "Implement src/training/trainer.py with CPU-optimized loop"
Task: "Create src/experiments/baseline_runner.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (T016)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently (T016) → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (T023) → Deploy/Demo
4. Add User Story 3 → Test independently (T030, T031A, T031B) → Deploy/Demo
5. Add Scaling Analysis (T040) → Quantify scaling exponent
6. Add Polish (Phase N) → Finalize documentation and artifacts
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Baseline) + T016
 - Developer B: User Story 2 (Microcircuit) + T023
 - Developer C: User Story 3 (Ablation/Scaling) + T030, T031A, T031B
3. Once US3 is stable:
 - Developer D: Scaling Analysis (T040)
4. Stories complete and integrate independently
5. No Phase 6/7 tasks (removed due to unapproved scope creep).

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Ensure all data generation is deterministic and checksummed (Constitution Principle III)
- **Critical**: Ensure all training runs respect CPU/RAM limits (FR-004) via `/usr/bin/time -v` in T014
- **Critical**: Ensure homeostatic scaling maintains 4:1 ratio dynamically (FR-002)
- **Critical**: T016 now records degradation metrics instead of enforcing a hard threshold.
- **Critical**: T030 now verifies statistical results without enforcing a specific effect size.
- **Critical**: T031A and T031B explicitly define the JSON schema for communication.
- **Critical**: T007 atomized into T007a, T007b, T007c for independent testability.
- **Critical**: Phase 6 and 7 removed as unapproved scope creep.
- **Critical**: T040 (Scaling Analyzer) now operates only on 1x/2x/4x variants as per FR-008.
- **Critical**: T007 (Microcircuit) no longer marked [P] to avoid resource contention.