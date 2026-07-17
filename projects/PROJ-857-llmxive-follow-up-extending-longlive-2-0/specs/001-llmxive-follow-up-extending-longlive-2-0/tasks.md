# Tasks: llmXive follow-up: extending "LongLive-2.0: An NVFP4 Parallel Infrastructure for Long Video Generation"

**Input**: Design documents from `/specs/001-llmxive-precision-threshold/`
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

- [X] T001 [P] Create project directories and files: `projects/PROJ-857-llmxive-follow-up-extending-longlive-2-0/code/`, `simulation/`, `evaluation/`, `analysis/`, `data/`, `tests/`, `data/results/`, and `__init__.py`, `config.py`, `requirements.txt` in respective directories

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Create `projects/PROJ-857-llmxive-follow-up-extending-longlive-2-0/code/requirements.txt` with dependencies: `torch`, `transformers`, `datasets`, `scikit-learn`, `numpy`, `pandas`, `matplotlib`, `seaborn`, `bayesian-optimization`, `psutil`, `scipy`
- [ ] T003 [P] Configure linting and formatting tools (black, flake8, isort)
- [ ] T004 [P] Implement `config.py` with constants for seeds, bit-widths (2, 4, 8), and path configurations
- [ ] T005 [P] Setup `data/loader.py` to stream Kinetics-400 subsets via `datasets.load_dataset(..., streaming=True)` with explicit error handling (fail loud, no synthetic fallback, no UCF101 fallback)
- [ ] T005a [P] Implement `data/downsampler.py` to extract 4-second clips and downsample the Kinetics-400 stream to fit within 7GB RAM, ensuring the transformation logic is explicit and reproducible
- [X] T006 [P] Create `data/__init__.py` and implement a cache eviction policy (LRU, configurable maximum size) to ensure dataset caching respects the 14GB disk limit.
- [ ] T007 [P] Implement `simulation/quantization_emulator.py` core logic using **stochastic rounding** (add uniform noise before floor/ceil) to emulate 2-bit, 4-bit, and 8-bit precision on 32-bit floats, ensuring noise distribution matches theoretical uniform within 5% KL-divergence (sample size N=10,000, computed via `scipy.stats.entropy`)
- [ ] T008 [P] Implement `simulation/student_model.py` wrapper for the simplified diffusion model compatible with CPU-only execution
- [ ] T009 [P] Setup `evaluation/clip_evaluator.py` to load a frozen CLIP-ViT model (no gradients) for temporal coherence scoring
- [ ] T038 Implement `data/discontinuity_generator.py` to programmatically generate a 'synthetic human-labeled subset' with known discontinuities (frame swaps/cuts) for validation. (Note: This task is NOT marked [P] as it is a strict prerequisite for T022).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - CPU-Only Precision Simulation Loop (Priority: P1) 🎯 MVP

**Goal**: Execute a complete training simulation loop on CPU-only environment modeling NVFP4 precision via stochastic rounding.

**Independent Test**: Run a single epoch on a downsampled Kinetics-400 subset; verify memory ≤ 7GB, disk ≤ 14GB, and stochastic noise distribution matches uniform within 5% KL-divergence.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 Implement unit test for stochastic rounding noise distribution in `tests/unit/test_quantization_emulator.py` (depends on T007; NOT marked [P] as it requires T007 completion)
- [X] T011 [P] [US1] Memory footprint test for training loop in `tests/unit/test_memory_footprint.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `simulation/training_loop.py` with CPU-only forward/backward pass using the **stochastic rounding logic from T007**
- [ ] T013 [US1] Integrate `data/downsampler.py` (T005a) into the training loop to fetch 4-second video clips via streaming
- [ ] T014 [US1] Add logic to dynamically switch bit-width (2, 4, 8) without code restart by re-initializing the quantization rounding logic via a factory function or re-instantiation of the emulator
- [ ] T015 [US1] Implement error handling for model collapse (NaN/Inf) to record "Collapse" status
- [ ] T017 [US1] Verify noise distribution matches theoretical uniform distribution within 5% KL-divergence (FR-009) using the N=10,000 sample size

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Narrative Consistency Evaluation Pipeline (Priority: P2)

**Goal**: Evaluate generated video sequences for temporal coherence using a frozen CLIP-ViT model.

**Independent Test**: Feed generated clips into the pipeline; verify output is a numeric score derived solely from the frozen evaluator with no gradient flow.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for consistency score output format in `tests/contract/test_evaluator.py`
- [X] T019 [P] [US2] Integration test for pipeline with injected discontinuity in `tests/integration/test_evaluator.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `evaluation/metrics.py` to calculate temporal coherence scores per video clip
- [ ] T021 [US2] Integrate `evaluation/clip_evaluator.py` with the training loop to score generated outputs
- [ ] T022 [US2] Implement validation logic for FR-007: compute Pearson correlation coefficient >= 0.7 between the model score and the **synthetic human-labeled subset** generated by T038 (frame swaps = 0.0, continuous = 1.0) on a held-out subset of 50 clips selected from the dataset
- [ ] T023 [US2] Ensure evaluation completes within 5 minutes per clip on CPU
- [ ] T024 [US2] Add handling for clips exceeding memory limits (abort with clear error or fallback to smaller subset)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Precision-Consistency Threshold Mapping (Priority: P3)

**Goal**: Aggregate results across bit-widths and seeds to identify the non-linear degradation threshold.

**Independent Test**: Run full experimental suite; verify output CSV contains bit-width, memory, convergence, and consistency score; statistical test identifies threshold with p < 0.05.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for regression model fitting in `tests/unit/test_aggregation.py`
- [ ] T026 [P] [US3] Integration test for full pipeline aggregation in `tests/integration/test_aggregation.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `analysis/aggregation.py` to collect results from varied bit-widths across multiple seeds
- [ ] T028 [US3] Implement `analysis/visualization.py` to generate precision-consistency curve and regression plots
- [ ] T029 [US3] Implement non-linear regression (piecewise linear with 2 segments using `scipy.optimize.curve_fit`) to model the precision-consistency data for bit-widths {2, 4, 8}
- [ ] T029a [US3] Implement the break-point detection algorithm in `analysis/aggregation.py` to identify the specific bit-width threshold where narrative consistency degrades non-linearly (FR-008)
- [ ] T030 [US3] Perform statistical analysis (paired t-tests, Bayesian Model Comparison) to validate significance (FR-005)
- [ ] T031 [US3] Generate final CSV output with all metrics and theoretical memory comparison (SC-005)
- [ ] T031a [US3] Implement the comparison logic to calculate the variance between theoretical memory footprint and runtime profiling (for internal validation only) and verify the <= 15% tolerance (SC-005)
- [ ] T032 [US3] Verify total execution time of full suite stays within 6-hour CI limit (SC-004)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033a [P] Update `README.md` with Installation, Usage, and Results sections including CLI arguments and example output
- [ ] T033b [P] Update `docs/` with API documentation and architecture diagrams
- [ ] T033c [P] Update `quickstart.md` with a runnable example script and expected output
- [ ] T034 Code cleanup and refactoring to ensure no GPU/CUDA instructions leak into CPU-only paths
- [ ] T035 Performance optimization for data streaming and model inference
- [ ] T036 [P] Additional unit tests for edge cases (model collapse, memory overflow)
- [ ] T037 Run quickstart.md validation and verify all artifacts are reproducible

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (generated clips) for evaluation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 outputs for aggregation

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
Task: "Memory footprint test for training loop in tests/unit/test_memory_footprint.py"

# Launch all models for User Story 1 together:
Task: "Implement simulation/training_loop.py with CPU-only forward/backward pass"
Task: "Integrate data/downsampler.py into the training loop to fetch 4-second video clips"
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