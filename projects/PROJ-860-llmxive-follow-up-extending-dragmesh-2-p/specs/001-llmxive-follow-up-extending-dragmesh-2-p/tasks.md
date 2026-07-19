# Tasks: llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

**Input**: Design documents from `/specs/001-virtual-tactile-adaptation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project Root**: `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/`
- **Source Code**: `code/` directory is nested inside the project root (e.g., `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/`)
- **Tests**: `tests/` directory is nested inside the project root (e.g., `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/`)
- **Data**: `data/` directory is nested inside the project root (e.g., `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/data/`)
- **State**: `state/` directory is nested inside the project root (e.g., `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/state/`)
- Paths shown below assume this nested project structure.

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

- [ ] T001 Create project structure per `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/` plan: Execute `mkdir -p code tests data/raw data/generated state/projects` and create `README.md` and `.gitignore` files.
- [ ] T002 Initialize Python project with `pybullet`, `numpy`, `scipy`, `pandas`, `datasets`, `pytest`, `statsmodels` in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/requirements.txt`: {{claim:c_f889aebb}}
- [ ] T003 [P] Configure `pytest-timeout` in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/pytest.ini`: Set `timeout=3600` for unit tests and `timeout=21600` for integration tests to enforce the 6h limit.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup CPU-only PyBullet physics environment in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/environment.py` (enforce `FR-004`, no CUDA)
 - **Requirement**: Insert a runtime check at the start of `environment.py` that explicitly verifies `torch.cuda.is_available()` is False (or PyBullet is not using GPU) and raises an error if any GPU backend is detected. (Merged T040)
- [X] T005 [P] Implement `VirtualTactileEstimator` class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/estimator.py` with moving average filter (window=5) and epsilon clamping (FR-001, FR-006, FR-007)
 - **Requirement**: Implement strict real-data fetcher in `code/data_loader.py` that explicitly fetches the DragMesh-2 manifest from the verified HuggingFace URL using `datasets.load_dataset`. This function MUST raise a `ConnectionError` or `FileNotFoundError` if the fetch fails; it MUST NOT include any `try/except` blocks that fall back to synthetic or placeholder data. (Merged T036)
 - **Requirement**: Add explicit "Stiction Handling" verification: Ensure the estimator applies a small epsilon ($\epsilon = 10^{-4}$) to the denominator to prevent division by zero, ensuring $k_{est}$ remains finite but high, triggering high detachment penalties. (Merged T039)
- [X] T006 [P] Implement `AdaptiveRewardScheduler` class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/scheduler.py` mapping $k_{est}$ to reward weights with EXPLICIT logic: if $k_{est} > 1.0$, increase $r_{detach}$ by ≥20%; if $k_{est} < 0.2$, decrease $r_{contact}$ by ≤15% (FR-002)
 - **Verification**: Include a self-test block in the task execution that prints the calculated $k_{est}$ and the resulting reward multiplier to prove the thresholds ($>1.0$, $<0.2$) are enforced before marking the task complete.
- [X] T007 [P] Create `NovelObjectSet` generator class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py` to produce a set of randomized articulated geometries with friction coefficients uniformly distributed across a broad range (FR-003). The class MUST accept `count` and `seed` arguments and output to `data/generated/`.
- [X] T008a [P] Implement seed fixation enforcement logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/seed_config.py` that explicitly sets seeds within the training (T012) and evaluation (T013) loops to ensure reproducibility (Constitution Principle I; FR-005)
- [X] T008b [P] Implement `validate_citations.py` script in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/validate_citations.py` (Constitution Principle II: Verified Accuracy)
- [ ] T009 [P] Setup state tracking in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` for artifact hashes: Initialize with `artifact_hashes: {}` and `updated_at: null`.
- [X] T009a [P] [DEPENDS ON T009] Implement checksum verification logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/checksum_verify.py`: Implement `sha256` hashing for all files in `data/raw` and `data/generated` and write results to the state YAML. (Constitution Principle III: Data Hygiene)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Zero-Shot Adaptation to Unseen Damping (Priority: P1) 🎯 MVP

**Goal**: Implement the full adaptive policy loop that detects friction via $k_{est}$ and adjusts rewards, verifying >15% improvement over static baseline on novel high-friction objects.

**Independent Test**: Run adaptive vs static policies on a set of novel objects with randomized friction (low to moderate). Verify paired t-test p-value < 0.05 and success rate improvement >15% for high-friction cases.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for `AdaptiveRewardScheduler` logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_scheduler.py` (verify weight scaling logic with explicit predefined thresholds)
- [X] T011 [P] [US1] Integration test for full pipeline (objects) in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/integration/test_pipeline.py` (verify success rate stats)

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `train.py` loop integrating `VirtualTactileEstimator` and `AdaptiveRewardScheduler` in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py`
- [X] T012c [US1] Implement `baseline_runner.py` to load and execute the static PICA baseline policy for comparison in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/baseline_runner.py`. The baseline MUST be loaded from the canonical HuggingFace dataset ID `dragmesh/pica-baseline-v` with a specific checkpoint hash (e.g., `sha256:PLACEHOLDER_HASH_UPDATE_AT_RUNTIME`). The implementer MUST verify and replace the placeholder hash with the actual verified hash from the registry before execution to ensure a verifiable comparison. (PRODUCER for T013 data) <!-- FAILED: unspecified -->
- [X] T013a [US1] [DEPENDS ON T007] Execute `generator.py` to produce a diverse set of novel geometry files in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/data/generated/`.: Run `python code/generator.py --count <N> --seed <SEED> --friction-min 0.1 --friction-max 2.0 --output data/generated/`. This task produces the 30 required artifacts for FR-003 and the paired t-test.
- [X] T013 [US1] [DEPENDS ON T012, T012c, T013a] Implement `evaluate.py` to run inference on novel objects using BOTH adaptive and static policies, logging success rates with EXPLICIT 'object_id' and 'policy_type' fields to preserve pairing structure for FR-005 in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/evaluate.py`.
 - **Requirement**: Explicitly check for the existence of `data/generated/` artifacts (produced by T013a) BEFORE attempting to load them. Add a pre-flight check that halts execution with a clear error message if the novel object set is missing. (Merged T037)
 - **Requirement**: Stream large result logs: Write results to `data/results/eval_logs.csv` in append mode (streaming) rather than accumulating all objects * 50 trials in memory. (Merged T038)
- [X] T014 [US1] [DEPENDS ON T013] Implement `aggregate.py` to collect and aggregate success rate data from evaluation logs into CSV format, ensuring 'object_id' is preserved for pairing in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/aggregate.py`.
- [X] T015 [US1] [DEPENDS ON T014] Implement `analysis.py` to perform paired t-test on aggregated data (using 'object_id' for pairing), calculate statistical power (effect size) to validate sample size, and assert p < 0.05 and >15% improvement in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/analysis.py`.
- [X] T016a [US1] Implement logging configuration in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/logging_config.py` with specific file paths and formats
- [X] T016b [US1] Add specific log statements for reward weight adjustments and $k_{est}$ values in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py`
- [X] T017 [US1] Verify `FR-001` formula implementation in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/estimator.py` (torque/velocity ratio)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Virtual Tactile Stiffness Estimation (Priority: P2)

**Goal**: Validate the $k_{est}$ estimator accuracy and stability under varying friction and noise conditions.

**Independent Test**: Inject known friction values, record torque/velocity derivatives, and verify linear correlation between $k_{est}$ and ground-truth friction. Verify stability under noise (moving average) and stiction (epsilon clamp).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for `VirtualTactileEstimator` division-by-zero protection in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_estimator.py`
- [X] T019 [P] [US2] Unit test for moving average filter smoothing in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_estimator.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement stress test script for `VirtualTactileEstimator` with noise injection in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/stress_test.py`
- [ ] T021 [US2] Implement validation script to correlate $k_{est}$ with ground-truth friction in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/validation.py`.
 - **Requirement**: Execute a sweep of **multiple randomized trials** with friction coefficients uniformly sampled from **[0.0, 2.5]** to verify linear correlation as per US2 Independent Test.
- [ ] T022 [US2] Integrate estimator validation into the main training loop in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py`
- [ ] T023 [US2] Verify `FR-007` clamping logic (bounded range) in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/estimator.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - CPU-Tractable Inference Pipeline (Priority: P3)

**Goal**: Ensure the entire experiment (data gen, training, eval, analysis) runs within 6 hours and 7GB RAM on a CPU-only runner.

**Independent Test**: Execute full pipeline on GitHub Actions free-tier runner with limited CPU and memory resources. Measure wall-clock time and peak memory. Verify no CUDA errors.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] CI workflow definition in `.github/workflows/test-cpu-pipeline.yml`: Define workflow with configurable timeout and memory limit checks.
- [ ] T025 [P] [US3] Implement memory profiling script in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/memory_profiler.py` using `tracemalloc` to capture and log PEAK memory usage (not average)

### Implementation for User Story 3

- [ ] T026 [P] [US3] Optimize `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py` for low memory usage during geometry generation
- [ ] T027 [US3] Optimize `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py` batch sizes and simulation steps to fit 6h limit
- [ ] T028a [US3] Create `code/run_benchmark.py` orchestration script: Implement a single executable script that orchestrates the full pipeline (generating data via T013a, training via T012, evaluating via T013, aggregating via T014) and outputs a summary JSON. (Addresses executability-74ded4dd)
- [ ] T029 [US3] Run full end-to-end benchmark: Execute `python code/run_benchmark.py --output data/results/benchmark_metrics.json`. Log wall-clock time and peak memory. **Do NOT assert limits here; only record metrics.** (SC-003, SC-004 Measurement)
- [ ] T029a [US3] Verify Success Criteria: Read `data/results/benchmark_metrics.json` and assert that wall-clock time <= 6h and peak memory <= 7GB. If limits are exceeded, log a warning but do not crash the pipeline (research outcome validation). (SC-003, SC-004 Validation)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/docs/` and `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/README.md`: Update 'Installation', 'Usage', and 'Results' sections with CLI examples and expected outputs.
- [ ] T031 Code cleanup and refactoring of `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/estimator.py` and `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/scheduler.py`
- [ ] T032 Performance optimization for simulation loop in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/environment.py`
- [ ] T033 [P] Additional unit tests for edge cases (stiction, extreme friction) in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/`
- [ ] T034 Run `quickstart.md` validation: Execute `python code/validate_quickstart.py` and verify exit code 0.
- [ ] T035 Verify `validate_citations.py` passes against all data sources

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Unit test for AdaptiveRewardScheduler logic in projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_scheduler.py"
Task: "Integration test for full pipeline (30 objects) in projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement train.py loop integrating VirtualTactileEstimator and AdaptiveRewardScheduler in projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py"
Task: "Implement evaluate.py to run inference on novel objects and log success rates in projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/evaluate.py"
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
- **CRITICAL**: All tasks must run on CPU-only free-tier CI (CPU, sufficient RAM, time limit). No GPU, no 8-bit/4-bit quantization.
- **CRITICAL**: Data loading tasks MUST fail loudly if the real source is unavailable; no synthetic fallbacks are permitted.
- **CRITICAL**: The estimator must strictly adhere to the sliding regime definition; stiction handling must be explicit via epsilon clamping, not by skipping the calculation entirely.
- **CRITICAL**: Task T013a (generation) MUST complete before T013 (evaluation) begins. The evaluation script must check for the existence of generated artifacts before proceeding.
- **CRITICAL**: T013a generates the specific diverse set for the t-test; T007 is the generic generator class, T013a is the execution.
- **RESOLVED**: T037 (Reorder task execution flow) is no longer a separate task; its logic (pre-flight check for generated artifacts) has been integrated into T013.