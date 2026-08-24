---
description: "Task list template for feature implementation"
---

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

- [X] T001a Create project directory structure per `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/` plan: Execute `mkdir -p code tests data/raw data/generated data/results state/projects` to establish the physical repository layout.
- [X] T001b Create empty skeleton files for project configuration: Create empty files `README.md`, `.gitignore`, and `code/requirements.txt` to establish file paths. **Do NOT populate content yet.**
- [X] T002 Populate `code/requirements.txt` with specific dependencies: Add `pybullet`, `numpy`, `scipy`, `pandas`, `datasets`, `pytest`, `statsmodels` with pinned versions to satisfy Constitution Principle I (Reproducibility). (DEPENDS ON T001b)
- [X] T003 Create `code/pytest.ini` with specific timeout configuration: Set `timeout=3600` for unit tests and `timeout=21600` for integration tests to enforce the 6h limit. (DEPENDS ON T001b)
- [X] T001c Compute SHA256 hashes for `README.md`, `.gitignore`, `requirements.txt` (from T002), and `pytest.ini` (from T003) and write them to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` under `artifact_hashes`. **Pre-check**: Verify all target files exist before checksumming. **Clarification**: Compute SHA256 of the *populated* `requirements.txt` and `pytest.ini` created in T002/T003, not the empty skeleton files. (DEPENDS ON T002, T003)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup CPU-only PyBullet physics environment in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/environment.py` (enforce `FR-004`, no CUDA)
 - **Requirement**: Insert a runtime check at the start of `environment.py` that explicitly verifies PyBullet is running in CPU mode by calling `pbd.useGPU(False)` and raising an error if GPU is detected. Do NOT use `torch.cuda.is_available()` as PyBullet does not rely on PyTorch.
- [X] T008b [P] Implement `validate_citations.py` script in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/validate_citations.py` (Constitution Principle II: Verified Accuracy)
- [X] T008c Execute `validate_citations.py` against DragMesh-2 and PICA baseline citations: Run the script to verify all citations in `plan.md` and `spec.md` before any data download tasks (T005d, T012d) are permitted. **Requirement**: If any citation fails validation, the pipeline must halt immediately. (DEPENDS ON T008b)
- [X] T005b Implement strict real-data fetcher verification logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/data_loader.py`
 - **Requirement**: Implement the code logic to verify the DragMesh-2 manifest fetched by T005d exists and is non-empty.
 - **Requirement**: This function MUST raise a `ConnectionError` or `FileNotFoundError` if the fetch fails; it MUST NOT include any `try/except` blocks that fall back to synthetic or placeholder data.
 - **Requirement**: This is a code implementation task only; it does not execute the check against real data.
 - **DEPENDS ON**: T001b, T002 (Code structure only).
- [X] T005d Download DragMesh-2 dataset from verified HuggingFace URL in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/data_loader.py`: Use `datasets.load_dataset` to fetch the DragMesh-2 manifest and data to `data/raw/`. **CI Setup Stage**: This task must be executed in a writable environment (local dev or CI setup stage) before the `data/raw` directory is mounted read-only in the production CI runner. **Error Handling**: MUST raise `ConnectionError` or `FileNotFoundError` if fetch fails; NO synthetic fallbacks. (DEPENDS ON T008c)
- [X] T005c Verify manifest integrity and record local checksum in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/verify_manifest.py`: Compute SHA256 of the fetched DragMesh-2 manifest. **Execute AFTER T005d**. **If the manifest is empty or missing, raise FileNotFoundError immediately.** If the file exists and is non-empty, record the hash to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` under `artifact_hashes` to satisfy **Constitution Principle III (Data Hygiene)** and ensure **FR-007** (clamping/stiction safety) by preventing downstream processing of invalid data. **Do NOT write to `data/raw/.checksums`** to respect read-only constraints. (DEPENDS ON T005d)
- [X] T005e Execute fetcher verification on fetched data in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/verify_manifest.py`: Run the verification logic implemented in T005b against the data fetched in T005d. **Requirement**: This task executes the check. If the manifest is missing or empty, it must raise an error and halt the pipeline. (DEPENDS ON T005d, T005c, T005b)
- [X] T005a Implement `VirtualTactileEstimator` class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/estimator.py`: Calculate $k_{est}$ using the given formula $k_{est} = \frac{|\Delta \tau_{hand}|}{|\Delta v_{object}|}$, incorporating a moving average filter (window size = 5) for smoothing torque derivatives (FR-006), and explicit epsilon clamping ($\epsilon = 10^{-4}$) and range clamping (bounded positive range) to handle zero object velocity and prevent numerical instability (FR-007). (FR-001, FR-006, FR-007)
- [X] T006 Implement `AdaptiveRewardScheduler` class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/scheduler.py` mapping $k_{est}$ to reward weights with EXPLICIT logic: if $k_{est} > 1.0$, increase $r_{detach}$ by ≥20%; if $k_{est} < 0.2$, decrease $r_{contact}$ by ≤15% (FR-002)
 - **Verification**: Include a self-test block in the task execution that prints the calculated $k_{est}$ and the resulting reward multiplier, and ASSERTS that the magnitude of the adjustment matches the spec's specific thresholds (>=20% increase, <=15% decrease).
- [X] T007 Create `NovelObjectSet` generator class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py` to produce a set of randomized articulated geometries with randomized friction coefficients for zero-shot evaluation (FR-003). The class MUST accept `count`, `seed`, `friction_min`, and `friction_max` arguments and output to `data/generated/`.
- [X] T008a Implement seed fixation enforcement logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/seed_config.py` that explicitly sets seeds for `numpy`, `random`, and `torch` (if used) to satisfy Constitution Principle I (Reproducibility). (Note: This sets global seeds before T012h and T013e run).
- [X] T009a Implement checksum verification logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/checksum_verify.py`: Compute SHA256 hashing function for files in `data/raw` and `data/generated`. (DEPENDS ON T001a)
- [X] T009c Execute checksum verification and update state: Run `checksum_verify.py` to hash all files in `data/raw` and `data/generated` and write results to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml`. (DEPENDS ON T005e, T009a)
- [X] T016a Create logging configuration in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/logging_config.py` with specific file paths and formats
- [X] T016b Add specific log statements for reward weight adjustments and $k_{est}$ values in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Zero-Shot Adaptation to Unseen Damping (Priority: P1) 🎯 MVP

**Goal**: Implement the full adaptive policy loop that detects friction via $k_{est}$ and adjusts rewards, verifying >15% improvement over static baseline on novel high-friction objects.

**Independent Test**: Run adaptive vs static policies on a set of novel objects with randomized friction (low to moderate). Verify paired t-test p-value < 0.05 and success rate improvement >15% for high-friction cases.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 Unit test for `AdaptiveRewardScheduler` logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_scheduler.py` (verify weight scaling logic with explicit predefined thresholds)
 - **Requirement**: The test MUST explicitly assert that for $k_{est} > 1.0$, the reward weight increases by >=20%, and for $k_{est} < 0.2$, the reward weight decreases by <=15%.

### Implementation for User Story 1

- [X] T012b Verify and fetch PICA baseline in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/baseline_fetcher.py`: Query the verified HuggingFace registry for the `dragmesh/pica-baseline-v` checkpoint, resolve the actual SHA256 hash, and write it to `data/raw/baseline/`. (DEPENDS ON T008c)
- [X] T012d Download PICA baseline policy in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/baseline_fetcher.py`: Download the baseline artifact resolved in T012b to `data/raw/baseline/`. **Strict Requirement**: This MUST write to `data/raw/baseline/`. Do NOT adapt paths to writable state directories. (DEPENDS ON T012b)
- [X] T012c Load and execute static PICA baseline policy in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/baseline_runner.py`: Load the baseline from the hash resolved in T012b and file downloaded in T012d. (DEPENDS ON T012b, T012d)
- [X] T012h Implement the training loop in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py` integrating `VirtualTactileEstimator` (T005a) and `AdaptiveRewardScheduler` (T006). **Requirement**: Assert CPU-only mode at runtime at the start of the loop to enforce **FR-004**. **Note**: This trains on the base DragMesh-2 dataset (not the novel object set) to produce the base model for zero-shot evaluation. (DEPENDS ON T005a, T006, T008a)
- [X] T013a Generate NovelObjectSet for zero-shot evaluation in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py`: Execute `python code/generator.py --count 30 --seed 42 --friction-min 0.1 --friction-max 1.2 --output data/generated/` to generate a dataset of sufficient size for the study. This task produces 30 objects with friction ranges covering low and high conditions. (DEPENDS ON T007)
- [X] T013b Verify generated artifacts exist and are valid in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/verify_generated.py`: Check that a sufficient number of files exist in `data/generated/`, are non-empty, and compute their SHA256 hashes to write to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml`. (DEPENDS ON T013a)
- [X] T013c Partition generated object set into subsets in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py`: Explicitly partition the generated set into a 'low_moderate' subset (friction in 0.1–0.7 range) and a 'high_friction' subset (0.8–1.2). Write a manifest file `data/generated/subsets.yaml` mapping object IDs to their friction category. (DEPENDS ON T013b)
- [X] T013d Implement pre-flight check for evaluation in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/evaluate.py`: Explicitly check for the existence of `data/generated/` artifacts (produced by T013b) and T013c validation success BEFORE attempting to load them. Add a pre-flight check that halts execution with a clear error message if the novel object set is missing or not diverse. (DEPENDS ON T013b, T013c)
- [X] T013e Implement inference runner in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/evaluate.py`: Run inference on novel objects using BOTH adaptive and static policies. **Requirement**: Assert CPU-only mode at runtime to enforce **FR-004**. **Requirement**: Read `data/generated/subsets.yaml` to tag results with 'low_moderate' or 'high_friction' labels. (DEPENDS ON T013d, T012c, T012h)
- [X] T013f Stream large result logs to `data/results/eval_logs.csv` in append mode rather than accumulating all objects * 50 trials in memory. Ensure 'object_id', 'policy_type', and 'friction_category' fields are preserved for pairing. (DEPENDS ON T013e)
- [X] T014 Implement `aggregate.py` to collect and aggregate success rate data from evaluation logs into CSV format, ensuring 'object_id' and 'friction_category' are preserved in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/aggregate.py`.
- [X] T015a Implement `t_test.py` to execute the paired t-test on aggregated data (using 'object_id' for pairing) as a distinct step for **FR-005**, calculating the t-statistic and raw p-value in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/t_test.py`.
- [X] T015b Implement `analysis.py` to collect t-test results, calculate statistical power (effect size) to validate sample size, and LOG the p-value and improvement percentages (DO NOT ASSERT) in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/analysis.py`. **Requirement**: Log `improvement_pct_low_moderate` and `improvement_pct_high_friction` separately.
- [X] T015c Validate analysis results: Create a separate script or CI step that reads the logged metrics from T015 and writes a JSON report `data/results/analysis_validation.json` containing `p_value`, `improvement_pct_low_moderate`, `improvement_pct_high_friction`, `pass_sc001` (bool, based on high_friction), and `pass_sc005` (bool). **DO NOT fail the script**; the goal is to record the result (positive or negative) for scientific analysis. The CI pipeline will fail at T015d. (DEPENDS ON T014, T013c)
- [X] T015d Validate statistical significance against **SC-005**: Read `data/results/analysis_validation.json` and verify `p_value < 0.05`. **Fail the CI pipeline if p-value >= 0.05**. Log the specific outcome.
- [X] T015e Validate high-friction improvement against SC-001: Read `data/results/analysis_validation.json` and verify that `improvement_pct_high_friction` (success rate improvement for the 'high_friction' subset 0.8–1.2) is at least 15%. Log the specific outcome. (Addresses SC-001) (DEPENDS ON T015b, T013c)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Virtual Tactile Stiffness Estimation (Priority: P2)

**Goal**: Validate the $k_{est}$ estimator accuracy and stability under varying friction and noise conditions.

**Independent Test**: Inject known friction values, record torque/velocity derivatives, and verify linear correlation between $k_{est}$ and ground-truth friction. Verify stability under noise (moving average) and stiction (epsilon clamp).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 Unit test for `AdaptiveRewardScheduler` logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_scheduler.py` (verify weight scaling logic with explicit predefined thresholds)
- [ ] T019 Unit test for moving average filter smoothing in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_estimator.py`

### Implementation for User Story 2

- [X] T020 Stress test script for `VirtualTactileEstimator` with noise injection in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/stress_test.py`
- [X] T021a Implement sweep generator script in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/sweep_generator.py`: Create a script that generates a CSV file with columns [trial_id, friction_value, torque_derivative, velocity_derivative] by simulating interactions with known friction values. The script must accept `n_trials`, `friction_min`, and `friction_max` arguments.
- [X] T021b Execute sweep with ground truth labels in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/sweep_generator.py`: Run the sweep generator with `n_trials=100`, `friction_min=0.0`, `friction_max=2.5`. Output file: `data/generated/sweep.csv`. **Requirement**: Ensure the generated data includes the exact ground-truth friction value used for each trial to enable correlation analysis. (DEPENDS ON T021a)
- [X] T021c Calculate linear correlation between $k_{est}$ and ground-truth friction from the sweep data generated in T021b in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/correlation_analysis.py`. (DEPENDS ON T021b)
- [X] T023 Verify FR-007 clamping logic via unit test `tests/unit/test_estimator_clamping.py`: assert that inputs outside [0.01, 10.0] result in outputs clamped to the bounds. (DEPENDS ON T005a)
- [X] T022 Integrate estimator validation into the main training loop in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py` (Moved from T022 to T022 to maintain sequence, previously T021d)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - CPU-Tractable Inference Pipeline (Priority: P3)

**Goal**: Ensure the entire experiment (data gen, training, eval, analysis) runs within 6 hours and 7GB RAM on a CPU-only runner.

**Independent Test**: Execute full pipeline on GitHub Actions free-tier runner with limited CPU and memory resources. Measure wall-clock time and peak memory. Verify no CUDA errors.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 CI workflow definition in `.github/workflows/test-cpu-pipeline.yml`: Define workflow with configurable timeout and memory limit checks.
- [ ] T025 Implement memory profiling script in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/memory_profiler.py` using `tracemalloc` to capture and log PEAK memory usage (not average)

### Implementation for User Story 3

- [X] T026 Optimize `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py` for low memory usage during geometry generation
- [X] T027 Optimize `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py` batch sizes and simulation steps to fit 6h limit
- [X] T028a Create `code/run_benchmark.py` orchestration script: Implement a single executable script that orchestrates the full pipeline (generating data via T013a, training via T012h, evaluating via T013e, aggregating via T014) and outputs a summary JSON.
- [X] T028b Create step wrappers in `code/run_benchmark.py`: Implement the individual step wrappers for generation, training, evaluation, and aggregation. (DEPENDS ON T028a)
- [X] T028c Generate summary JSON from step results: Generate the final summary JSON from the results of the step wrappers. (DEPENDS ON T028b)
- [X] T029 Run full end-to-end benchmark: Execute `python code/run_benchmark.py --output data/results/benchmark_metrics.json`. Log wall-clock time and peak memory. **Do NOT assert limits here; only record metrics.** (SC-003, SC-004 Measurement)
- [X] T029b Record benchmark results: Read `data/results/benchmark_metrics.json` and write a JSON report `data/results/benchmark_report.json` containing `wall_clock_time`, `peak_memory_gb`, `pass_sc003` (bool), and `pass_sc004` (bool). **Do NOT assert limits or exit non-zero.** If limits are exceeded, log a warning but continue to allow analysis of why the method failed tractability.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 Documentation updates in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/docs/` and `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/README.md`: Update 'Installation', 'Usage', and 'Results' sections with CLI examples and expected outputs.
- [ ] T031 Code cleanup and refactoring of `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/estimator.py` and `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/scheduler.py`
- [ ] T032 Performance optimization for simulation loop in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/environment.py`
- [ ] T033 Additional unit tests for edge cases (stiction, extreme friction) in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/`
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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other user stories
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
- Different user stories can be worked on in parallel by different team members

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
- **RESOLVED**: T037 (Reorder task execution flow) is no longer a separate task; its logic has been integrated into T013d.
- **RESOLVED**: T015 (Analysis) now separates measurement (T015) from validation (T015b).
- **RESOLVED**: T029b logs metrics without blocking execution, allowing analysis of tractability failures.
- **FIXED**: T004 now correctly checks PyBullet's CPU backend flag.
- **FIXED**: T005b [P] tag removed.
- **FIXED**: T008c enforces Verified Accuracy gate before data download.
- **FIXED**: T012h explicitly states it trains on base data, not novel set.
- **FIXED**: T005b description clarifies it is code implementation only.
- **FIXED**: T005c now implements and runs separate steps.
- **FIXED**: T013a generates friction metadata for partitioning.
- **FIXED**: Removed [P] tags from tasks with dependencies.
- **ADDED**: Additional implementation tasks to address missing logic.
- **FIXED**: T021a split into T021a (generator) and T021b (execution with N=100, range 0.0-2.5).
- **FIXED**: T015b/T015c/T015d/T015e now explicitly track 'high_friction' (0.8-1.2) subset for SC-001.
- **FIXED**: T001c clarified to hash populated files.
- **FIXED**: T005a moved to Phase 2 to ensure estimator exists before T012h.
- **FIXED**: T005d and T005c now precede T005e to ensure data artifacts exist before verification.