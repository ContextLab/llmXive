# Tasks: llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

**Input**: Design documents from `/specs/001-virtual-tactile-adaptation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create project directory structure per `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/` plan: Execute `mkdir -p code tests data/raw data/generated data/results state/projects` to establish the physical repository layout.
- [X] T001b Create empty skeleton files for project configuration: Create empty files `README.md`, `.gitignore`, and `code/requirements.txt` to establish file paths. **Do NOT populate content yet.**
- [X] T002 Populate `code/requirements.txt` with specific dependencies: Add `pybullet`, `numpy`, `scipy`, `pandas`, `datasets`, `pytest`, `statsmodels` with pinned versions to satisfy Constitution Principle I (Reproducibility). (DEPENDS ON T001b)
- [X] T003 Create `code/pytest.ini` with specific timeout configuration: Set `timeout=3600` for unit tests and `timeout=21600` for integration tests to enforce the 6h limit. (DEPENDS ON T001b)
- [ ] T001c Generate checksums for code/config artifacts in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/checksum_config.py`: Compute SHA256 hashes for `README.md`, `.gitignore`, `requirements.txt` (from T002), and `pytest.ini` (from T003) and write them to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` under `artifact_hashes`. **Pre-check**: Verify all target files exist before checksumming. (DEPENDS ON T002, T003, T001a, T001b)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup CPU-only PyBullet physics environment in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/environment.py` (enforce `FR-004`, no CUDA)
 - **Requirement**: Insert a runtime check at the start of `environment.py` that explicitly verifies PyBullet is running in CPU mode by calling `pbd.useGPU(False)` and raising an error if GPU is detected. Do NOT use `torch.cuda.is_available()` as PyBullet does not rely on PyTorch.
- [ ] T005d [P] Download DragMesh-2 dataset from verified HuggingFace URL in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/data_loader.py`: Use `datasets.load_dataset` to fetch the DragMesh-2 manifest and data to `data/raw/`. **CI Setup Stage**: This task must be executed in a writable environment (local dev or CI setup stage) before the `data/raw` directory is mounted read-only in the production CI runner. **Error Handling**: MUST raise `ConnectionError` or `FileNotFoundError` if fetch fails; NO synthetic fallbacks.
- [ ] T005c Verify manifest integrity and record local checksum in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/verify_manifest.py`: Compute SHA256 of the fetched DragMesh-2 manifest. **If the manifest is empty, raise FileNotFoundError immediately.** If the file exists and is non-empty, record the hash to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` under `artifact_hashes.data_raw` to satisfy **Constitution Principle III (Data Hygiene)** and ensure **FR-007** (clamping/stiction safety) by preventing downstream processing of invalid data. **Do NOT write to `data/raw/.checksums`** to respect read-only constraints. (DEPENDS ON T005d)
- [ ] T005b [P] Implement strict real-data fetcher verification in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/data_loader.py`
 - **Requirement**: Explicitly verify the DragMesh-2 manifest fetched by T005d exists and is non-empty.
 - **Requirement**: This function MUST raise a `ConnectionError` or `FileNotFoundError` if the fetch fails; it MUST NOT include any `try/except` blocks that fall back to synthetic or placeholder data.
 - **DEPENDS ON**: T005c (Data must be verified before fetcher verification completes).
- [X] T005a [P] Implement `VirtualTactileEstimator` class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/estimator.py` (FR-001, FR-006, FR-007)
 - **Requirement**: Implement the core formula $k_{est} = \frac{|\Delta \tau_{hand}|}{|\Delta v_{object}|}$ using numpy.
 - **Requirement**: Implement a moving average filter (window size = 5) on the torque derivative signal before computing the ratio.
 - **Requirement**: Implement stiction handling: apply a small epsilon ($\epsilon = 10^{-4}$) to the denominator to prevent division by zero, ensuring $k_{est}$ remains finite but high.
 - **Requirement**: Implement clamping of $k_{est}$ to a physically meaningful positive range to prevent numerical instability.
- [X] T006 [P] Implement `AdaptiveRewardScheduler` class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/scheduler.py` mapping $k_{est}$ to reward weights with EXPLICIT logic: if $k_{est} > 1.0$, increase $r_{detach}$ by ≥20%; if $k_{est} < 0.2$, decrease $r_{contact}$ by ≤15% (FR-002)
 - **Verification**: Include a self-test block in the task execution that prints the calculated $k_{est}$ and the resulting reward multiplier, and ASSERTS that the magnitude of the adjustment matches the spec's specific thresholds (>=20% increase, <=15% decrease).
- [X] T007 [P] Create `NovelObjectSet` generator class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py` to produce a set of randomized articulated geometries with friction coefficients uniformly distributed across a broad range (FR-003). The class MUST accept `count`, `seed`, `friction_min`, and `friction_max` arguments and output to `data/generated/`.
- [X] T008a [P] Implement seed fixation enforcement logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/seed_config.py` that explicitly sets seeds for `numpy`, `random`, and `torch` (if used) to satisfy Constitution Principle I (Reproducibility). (Note: This sets global seeds before T012f and T013e run).
- [X] T008b [P] Implement `validate_citations.py` script in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/validate_citations.py` (Constitution Principle II: Verified Accuracy)
- [ ] T009a [P] Implement checksum verification logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/checksum_verify.py`: Implement `sha256` hashing function for files in `data/raw` and `data/generated`. (DEPENDS ON T001a, T001b)
- [ ] T009c Execute checksum verification and update state: Run `checksum_verify.py` to hash all files in `data/raw` and `data/generated` and write results to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml`. (DEPENDS ON T005c, T009a)
- [X] T016a [P] Implement logging configuration in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/logging_config.py` with specific file paths and formats
- [ ] T016b [P] Add specific log statements for reward weight adjustments and $k_{est}$ values in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Zero-Shot Adaptation to Unseen Damping (Priority: P1) 🎯 MVP

**Goal**: Implement the full adaptive policy loop that detects friction via $k_{est}$ and adjusts rewards, verifying >15% improvement over static baseline on novel high-friction objects.

**Independent Test**: Run adaptive vs static policies on a set of novel objects with randomized friction (low to moderate). Verify paired t-test p-value < 0.05 and success rate improvement >15% for high-friction cases.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for `AdaptiveRewardScheduler` logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_scheduler.py` (verify weight scaling logic with explicit predefined thresholds)
 - **Requirement**: The test MUST explicitly assert that for $k_{est} > 1.0$, the reward weight increases by >=20%, and for $k_{est} < 0.2$, the reward weight decreases by <=15%.

### Implementation for User Story 1

- [ ] T012b Verify and fetch PICA baseline in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/baseline_fetcher.py`: Query the verified HuggingFace registry for the `dragmesh/pica-baseline-v` checkpoint, resolve the actual SHA256 hash, and write it to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` under `artifact_hashes` for `baseline`. (DEPENDS ON T008b)
- [ ] T012d Download PICA baseline policy in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/baseline_fetcher.py`: Download the baseline artifact resolved in T012b to `data/raw/baseline/`. **Strict Requirement**: This MUST write to `data/raw/baseline/`. Do NOT adapt paths to writable state directories. (DEPENDS ON T012b)
- [ ] T012c Load and execute static PICA baseline policy in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/baseline_runner.py`: Load the baseline from the hash resolved in T012b and file downloaded in T012d. (DEPENDS ON T012b, T012d)
- [ ] T012f [P] [US1] Implement `VirtualTactileEstimator` integration in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py`. (DEPENDS ON T005a)
- [ ] T012g [US1] Implement `AdaptiveRewardScheduler` integration in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py`. (DEPENDS ON T006, T012f)
- [ ] T012h [US1] Implement the training loop in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py` integrating T012f and T012g. **Requirement**: Assert CPU-only mode at runtime at the start of the loop to enforce **FR-004**. (DEPENDS ON T012f, T012g)
- [ ] T013a Generate and link NovelObjectSet for zero-shot evaluation in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py`: Execute `python code/generator.py --count 30 --seed 42 --friction-min 0.1 --friction-max 1.2 --output data/generated/` to generate a dataset of sufficient size for the study. This task produces the 30 required artifacts for FR-003 with specific friction ranges covering low (0.1-0.3) and high (0.8-1.2) conditions. (DEPENDS ON T007)
- [ ] T013b Verify generated artifacts exist and are valid in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/verify_generated.py`: Check that a sufficient number of files exist in `data/generated/`, are non-empty, and compute their SHA256 hashes to write to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml`. (DEPENDS ON T013a)
- [ ] T013c [US1] Validate diversity of generated object set in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/validate_diversity.py`: Verify that the generated friction coefficients cover the full range of expected values. with a uniform distribution (histogram check). Raise ValueError if the set is not diverse. (DEPENDS ON T013b)
- [ ] T013d [US1] Implement pre-flight check for evaluation in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/evaluate.py`: Explicitly check for the existence of `data/generated/` artifacts (produced by T013b) and T013c validation success BEFORE attempting to load them. Add a pre-flight check that halts execution with a clear error message if the novel object set is missing or not diverse. (DEPENDS ON T013b, T013c)
- [ ] T013e [US1] Implement inference runner in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/evaluate.py`: Run inference on novel objects using BOTH adaptive and static policies. **Requirement**: Assert CPU-only mode at runtime to enforce FR-004. (DEPENDS ON T013d, T012c, T012h)
- [ ] T013f [US1] Implement streaming log handler in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/evaluate.py`: Stream large result logs to `data/results/eval_logs.csv` in append mode rather than accumulating all objects * 50 trials in memory. Ensure 'object_id' and 'policy_type' fields are preserved for pairing. (DEPENDS ON T013e)
- [ ] T014 [US1] [DEPENDS ON T013f] Implement `aggregate.py` to collect and aggregate success rate data from evaluation logs into CSV format, ensuring 'object_id' is preserved for pairing in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/aggregate.py`.
- [ ] T015a [US1] [DEPENDS ON T014] Implement `t_test.py` to execute the paired t-test on aggregated data (using 'object_id' for pairing) as a distinct step for **FR-005**, calculating the t-statistic and raw p-value in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/t_test.py`.
- [ ] T015 [US1] [DEPENDS ON T015a] Implement `analysis.py` to collect t-test results, calculate statistical power (effect size) to validate sample size, and LOG the p-value and improvement percentage (DO NOT ASSERT) in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/analysis.py`. (Measurement only)
- [ ] T015b [US1] Validate analysis results: Create a separate script or CI step that reads the logged metrics from T015 and writes a JSON report `data/results/analysis_validation.json` containing `p_value`, `improvement_pct`, `pass_sc001` (bool), and `pass_sc005` (bool). **DO NOT fail the script**; the goal is to record the result (positive or negative) for scientific analysis. The CI pipeline will fail at T015c.
- [ ] T015c [US1] Validate statistical significance against **SC-005**: Read `data/results/analysis_validation.json` and verify `p_value < 0.05`. **Fail the CI pipeline if p-value >= 0.05**. Log the specific outcome.
- [ ] T015d [US1] Validate varying friction improvement against SC-002: Read `data/results/analysis_validation.json` and verify that the success rate improvement for the 'varying friction' subset is at least 10%. Log the specific outcome. (Addresses SC-002)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Virtual Tactile Stiffness Estimation (Priority: P2)

**Goal**: Validate the $k_{est}$ estimator accuracy and stability under varying friction and noise conditions.

**Independent Test**: Inject known friction values, record torque/velocity derivatives, and verify linear correlation between $k_{est}$ and ground-truth friction. Verify stability under noise (moving average) and stiction (epsilon clamp).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for `VirtualTactileEstimator` division-by-zero protection in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_estimator.py`
- [ ] T019 [P] [US2] Unit test for moving average filter smoothing in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_estimator.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement stress test script for `VirtualTactileEstimator` with noise injection in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/stress_test.py`
- [ ] T021a [US2] Implement data generation/sweep execution script in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/stress_test.py`: Execute a sweep of **multiple randomized trials** with friction coefficients uniformly sampled from a **non-negative range** to generate data for correlation analysis.
- [ ] T021b [US2] Implement correlation calculation logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/validation.py`: Calculate linear correlation between $k_{est}$ and ground-truth friction from the sweep data generated in T021a.
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
- [ ] T028b [US3] Create `code/run_benchmark.py` orchestration script: Implement a single executable script that orchestrates the full pipeline (generating data via T013a, training via T012h, evaluating via T013e, aggregating via T014) and outputs a summary JSON.
- [ ] T028c [US3] Implement step wrappers in `code/run_benchmark.py`: Implement the individual step wrappers for generation, training, evaluation, and aggregation. (DEPENDS ON T028b)
- [ ] T028d [US3] Implement summary JSON generation in `code/run_benchmark.py`: Generate the final summary JSON from the results of the step wrappers. (DEPENDS ON T028c)
- [ ] T029 [US3] Run full end-to-end benchmark: Execute `python code/run_benchmark.py --output data/results/benchmark_metrics.json`. Log wall-clock time and peak memory. **Do NOT assert limits here; only record metrics.** (SC-003, SC-004 Measurement)
- [ ] T029b [US3] Record benchmark results: Read `data/results/benchmark_metrics.json` and write a JSON report `data/results/benchmark_report.json` containing `wall_clock_time`, `peak_memory_gb`, `pass_sc003` (bool), and `pass_sc004` (bool). **Do NOT assert limits or exit non-zero.** If limits are exceeded, log a warning but continue to allow analysis of why the method failed tractability. (SC-003, SC-004 Recording only)

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
Task: "Implement VirtualTactileEstimator integration in projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py"
Task: "Implement AdaptiveRewardScheduler integration in projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py"
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
- **CRITICAL**: Task T013a (generation) MUST complete before T013e (evaluation) begins. The evaluation script must check for the existence of generated artifacts before proceeding.
- **CRITICAL**: T013a generates the specific diverse set for the t-test; T007 is the generic generator class, T013a is the execution.
- **RESOLVED**: T037 (Reorder task execution flow) is no longer a separate task; its logic (pre-flight check for generated artifacts) has been integrated into T013d.
- **RESOLVED**: T015 (Analysis) now separates measurement (T015) from validation (T015b) to allow recording of negative results.
- **RESOLVED**: T029b (Benchmark) now records metrics without blocking execution, allowing analysis of tractability failures.
- **RESOLVED**: T004 now correctly checks PyBullet's CPU backend flag.
- **RESOLVED**: T005 is split into T005a (Estimator) and T005b (Fetcher) to address scope conflation.
- **RESOLVED**: T013a uses explicit numeric friction ranges (0.1-1.2) to satisfy US-1 boundary conditions.
- **RESOLVED**: T005c ensures checksums are recorded locally in `state/projects/...` per Constitution Principle III.
- **RESOLVED**: T012a explicitly links the novel object set generation to the zero-shot evaluation requirement.
- **RESOLVED**: Tc (Power Analysis) added to justify sample size of 30.
- **REVISED**: T013a friction range expanded to 0.1–1.2 (US-1) with explicit high-friction subset (0.8–1.2) for SC-001 verification.
- **REVISED**: T021 friction sweep expanded to [0.0, 2.5] to cover edge cases and verify linear correlation across a broader physical regime.
- **REVISED**: T015b validation logic clarified to log failure without blocking execution, ensuring negative results are recorded for analysis.
- **ADDED**: T005d (Download DragMesh-2) to ensure data availability.
- **ADDED**: T012d (Download Baseline) to ensure baseline availability.
- **FIXED**: T012c description to correctly reference T012b and T012d.
- **FIXED**: T001a to be a single explicit command.
- **FIXED**: T008a to be explicit about seeding libraries.
- **FIXED**: T012a removed to avoid redundancy.
- **FIXED**: T005c to respect read-only constraints.
- **FIXED**: T001c to depend on T002 and T003 to resolve ordering.
- **FIXED**: T008a tag to Constitution Principle I.
- **FIXED**: T015b to remove 'assert' instruction.
- **FIXED**: T005b to depend on T005c.
- **FIXED**: T001b to create only skeletons, resolving semantic conflict.
- **FIXED**: T001c [P] tag removed.
- **FIXED**: T005b [P] tag removed.
- **FIXED**: T009c [P] tag removed.
- **FIXED**: T012c [P] tag removed.
- **ADDED**: T012f, T012g, T012h to atomize training loop.
- **ADDED**: T013c to validate diversity.
- **ADDED**: T013d, T013e, T013f to atomize evaluation.
- **ADDED**: T015d to validate SC-002.
- **ADDED**: T021a, T021b to atomize validation.
- **ADDED**: T028b, T028c, T028d to atomize benchmark.
- **FIXED**: Ordering of T005d -> T005c -> T005b.
- **FIXED**: Removed self-reference in T009a.
- **FIXED**: Removed stale IDs (coverage-*, constraint_preservation-*) from all tasks.
- **FIXED**: Removed [P] tags from T012g, T012h, T013d, T028c, T028d where dependencies exist.
- **FIXED**: T012d to strictly enforce `data/raw/baseline/` path.
