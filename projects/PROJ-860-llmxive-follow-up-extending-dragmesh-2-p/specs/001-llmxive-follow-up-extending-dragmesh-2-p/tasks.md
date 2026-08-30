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
 - **Requirement**: Insert a **global** runtime check at the start of `environment.py` that explicitly verifies PyBullet is running in CPU mode by calling `pbd.configureDebugVisualizer(pbd.COV_ENABLE_GUI,0)` and ensuring no CUDA flags are set; raise an error if GPU usage is detected. This check must abort the process if CUDA is detected.
- [X] T008b [P] Implement `validate_citations.py` script in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/validate_citations.py` (Constitution Principle II: Verified Accuracy)
- [X] T008c Execute `validate_citations.py` against DragMesh-2 and PICA baseline citations: Run the script to verify all citations in `plan.md` and `spec.md` before any data download tasks (T005d, T012d) are permitted. **Requirement**: If any citation fails validation, the pipeline must halt immediately with a non-zero exit code. **Output**: Generate `citations_validation.log` in `data/results/` containing the validation status and any errors. (DEPENDS ON T008b)
- [X] T005b Implement strict real-data fetcher verification logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/data_loader.py`
 - **Requirement**: Add function `def verify_manifest_integrity(manifest_path: str) -> None:` that checks existence, non‑emptiness, and raises `FileNotFoundError` or `ConnectionError` on failure. No synthetic fallback. (DEPENDS ON T001b, T002)
- [X] T005d Download DragMesh-2 dataset from verified HuggingFace URL in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/data_loader.py`: Use `datasets.load_dataset` to fetch the DragMesh-2 manifest and data to `data/raw/`. **CI Setup Stage**: This task must be executed in a writable environment (local dev or CI setup stage) before the `data/raw` directory is mounted read‑only in the production CI runner. **Error Handling**: MUST raise `ConnectionError` or `FileNotFoundError` if fetch fails; NO synthetic fallbacks. (DEPENDS ON T008c)
- [X] T005c Verify manifest integrity and record local checksum in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/verify_manifest.py`: Compute SHA256 of `data/raw/dataset_manifest.jsonl`. **Execute AFTER T005d**. **Requirement**: If the manifest is missing or empty, raise `FileNotFoundError` immediately and halt. If the file exists and is non‑empty, record the hash to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml` under the key `artifact_hashes.data_raw` (NOT `data_raw_manifest`). (DEPENDS ON T005d)
- [X] T005e Execute fetcher verification on fetched data in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/verify_manifest.py`: Run `verify_manifest_integrity('data/raw/dataset_manifest.jsonl')`. **Requirement**: This task executes the check. If the manifest is missing or empty, it must raise an error and halt the pipeline. (DEPENDS ON T005d, T005c, T005b)
- [X] T005a Implement `VirtualTactileEstimator` class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/estimator.py`: Calculate $k_{est}$ using the given formula $k_{est} = \frac{|\Delta \tau_{hand}|}{|\Delta v_{object}|}$, incorporating a **moving average filter (window size = 5) applied to the torque signal BEFORE computing the derivative** (FR-006), epsilon clamping ($\epsilon = 10^{-4}$) and range clamping to a positive bounded interval (FR-007). (FR-001, FR-006, FR-007)
- [X] T006 Implement `AdaptiveRewardScheduler` class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/scheduler.py` mapping $k_{est}$ to reward weights with EXPLICIT logic: if $k_{est} > 1.0$, increase $r_{detach}$ by ≥20%; if $k_{est} < 0.2$, decrease $r_{contact}$ by ≤15% (FR-002)
 - **Verification**: Include a self‑test block that prints the calculated $k_{est}$ and the resulting reward multiplier, and ASSERTS that the magnitude of the adjustment matches the spec's thresholds.
- [X] T007 Create `NovelObjectSet` generator class in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py` to produce a set of randomized articulated geometries with randomized friction coefficients for zero‑shot evaluation (FR-003). The class MUST accept `count`, `seed`, `friction_min`, and `friction_max` arguments and output to `data/generated/`.
- [X] T008a Implement seed fixation enforcement logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/seed_config.py` that explicitly sets seeds for `numpy`, `random`, and `torch` (if used) to satisfy Constitution Principle I (Reproducibility). (Note: This sets global seeds before T012h and T013e run).
- [X] T009a Implement checksum verification logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/checksum_verify.py`: Compute SHA256 hashing function for files in `data/raw` and `data/generated`. (DEPENDS ON T001a)
- [X] T009c Execute checksum verification and update state: Run `checksum_verify.py` to hash all files in `data/raw` and `data/generated` and write results to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml`. (DEPENDS ON T005f, T009a)
- [X] T016a Create logging configuration in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/logging_config.py` with specific file paths and formats
- [X] T016b Add specific log statements for reward weight adjustments and $k_{est}$ values in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py`: **Requirement**: Logs MUST include the specific configuration constants used: `epsilon=1e-4` and `filter_window=5` alongside runtime values to ensure reproducibility (Constitution Principle I).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Zero-Shot Adaptation to Unseen Damping (Priority: P1) 🎯 MVP

**Goal**: Implement the full adaptive policy loop that detects friction via $k_{est}$ and adjusts rewards, verifying >15% improvement over static baseline on novel high‑friction objects.

**Independent Test**: Run adaptive vs static policies on a set of novel objects with randomized friction (low to moderate). Verify GLMM p‑value < 0.05 and success‑rate improvement >15% for high‑friction cases.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 Unit test for `AdaptiveRewardScheduler` logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_scheduler.py` (verify weight scaling logic with explicit predefined thresholds)
 - **Requirement**: The test MUST explicitly assert that for $k_{est} > 1.0$, the reward weight increases by >=20%, and for $k_{est} < 0.2$, the reward weight decreases by <=15%.

### Implementation for User Story 1

- [X] T012b Verify and fetch PICA baseline in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/baseline_fetcher.py`: Query the verified HuggingFace registry for the `dragmesh/pica-baseline-v` checkpoint, resolve the actual SHA256 hash, and write it to `data/raw/baseline/`. (DEPENDS ON T008d)
- [X] T012d Download PICA baseline policy in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/baseline_fetcher.py`: Download the baseline artifact resolved in T012b to `data/raw/baseline/`. **Strict Requirement**: This MUST write to `data/raw/baseline/`. Do NOT adapt paths to writable state directories. (DEPENDS ON T012b)
- [X] T012c Load and validate static PICA baseline policy in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/baseline_runner.py`: Load the baseline from the hash resolved in T012b and file downloaded in T012d. **Requirement**: This is a dry-run/validation step only to ensure the model loads correctly; it does NOT execute the full evaluation. (DEPENDS ON T012b, T012d)
- [X] T012h Implement the training loop in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py` integrating `VirtualTactileEstimator` (T005a) and `AdaptiveRewardScheduler` (T006). **Requirement**: Assert CPU‑only mode at runtime at the start of the loop to enforce **FR-004**. **Note**: This trains on the base DragMesh‑2 dataset **EXCLUDING** any objects with friction in the 0.8–1.2 range (pre‑training filter added) to ensure the 0.8–1.2 objects in T013a are truly novel. **Integration**: The estimator validation and reward adjustment logic is implemented directly within this loop (replaces T022). (DEPENDS ON T005a, T006, T008a)
- [X] T013a Generate NovelObjectSet for zero‑shot evaluation in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py`: Execute `python code/generator.py --count --seed 42 --high-friction-count 25 --friction-min 0.0 --friction-max 2.5 --output data/generated/` to produce **25 high‑friction objects (friction 0.8–1.2)** and **25 objects covering the full friction range (0.0–2.5)**. **Requirement**: Explicitly use `seed=42` for deterministic generation. (DEPENDS ON T007)
- [X] T013b Verify generated artifacts exist and are valid in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/verify_generated.py`: Check that at least 50 files exist in `data/generated/`, are non‑empty, and compute their SHA256 hashes to write to `state/projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml`. (DEPENDS ON T013a)
- [X] T013c Partition generated object set into subsets in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py`: Write manifest `data/generated/subsets.yaml` mapping each object ID to `high_friction` or `low_moderate` based on its friction coefficient. (DEPENDS ON T013b)
- [X] T013d Implement pre‑flight check for evaluation in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/evaluate.py`: Verify existence of `data/generated/` artifacts and successful execution of T013c before proceeding. Halt with clear error if missing or insufficient diversity. (DEPENDS ON T013b, T013c)
- [X] T013e Implement inference runner in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/evaluate.py`: Run inference on novel objects using BOTH adaptive and static policies. **Requirement**: Assert CPU‑only mode at runtime. Read `data/generated/subsets.yaml` to tag results with friction category. Output per‑trial rows to `data/results/eval_logs.csv` with columns `trial_id,object_id,policy_type,friction_category,success,k_est`. (DEPENDS ON T013d, T012h)
- [X] T013f Stream large result logs to `data/results/eval_logs.csv` in append mode rather than accumulating all objects × 50 trials in memory. Ensure columns `object_id`, `policy_type`, and `friction_category` are preserved for pairing. (DEPENDS ON T013e)
- [X] T014 Implement `aggregate.py` to collect and aggregate success‑rate data from `eval_logs.csv` into `data/results/aggregated.csv`, preserving `object_id` and `friction_category`. (DEPENDS ON T013f)
- [X] T015a Implement GLMM analysis in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/glmm_analysis.py`: Use `statsmodels` to fit a **Generalized Linear Mixed Model (GLMM)** on `data/results/aggregated.csv` (columns: `object_id`, `policy_type`, `success`, `friction_category`). **Note**: This replaces the "paired t-test" mandated by FR-005/SC-005 because the GLMM is required to handle zero-success baselines robustly. **Output**: Model summary to `data/results/glmm_summary.json` including p‑value and **Odds Ratios**. (DEPENDS ON T014)
- [X] T015b Implement `analysis.py` to read `glmm_summary.json`, extract overall p‑value and odds ratios for high‑friction subset, and write a concise JSON report `data/results/analysis_glmm.json` with fields `p_value`, `odds_ratio_high`, `improvement_pct_high_friction`. (DEPENDS ON T015a)
- [X] T015c Validate analysis results: Read `data/results/analysis_glmm.json` and write a verification JSON `data/results/analysis_validation.json` containing `p_value`, `improvement_pct_high_friction`, and boolean flags `pass_sc001` (improvement ≥15%) and `pass_sc005` (p_value < 0.05). (DEPENDS ON T015b)
- [X] T015d Validate statistical significance against **SC-005**: Read `data/results/analysis_validation.json` and FAIL the CI if `p_value >= 0.05`. Log the specific outcome. **Note**: This validates the GLMM p-value, which replaces the t-test p-value as per the plan's methodological update. (DEPENDS ON T015c)
- [X] T015e Validate high‑friction improvement against **SC-001**: Read `data/results/analysis_validation.json` and FAIL the CI if `improvement_pct_high_friction < 15`. Log the specific outcome. (DEPENDS ON T015c)
- [X] T015f Update spec.md to reflect GLMM replacement: Edit `specs/001-virtual-tactile-adaptation/spec.md` to update FR-005 and SC-005 to explicitly state that a GLMM is used instead of a paired t-test to handle zero-success baselines, ensuring the spec matches the implementation. (DEPENDS ON T015a)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Virtual Tactile Stiffness Estimation (Priority: P2)

**Goal**: Validate the $k_{est}$ estimator accuracy and stability under varying friction and noise conditions.

**Independent Test**: Inject known friction values, record torque/velocity derivatives, and verify linear correlation between $k_{est}$ and ground‑truth friction. Verify stability under noise (moving average) and stiction (epsilon clamp).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T036 Unit test for moving average filter logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_estimator_filter.py` (Consolidated into T033)
- [ ] T037 Unit test for epsilon clamping logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_estimator_epsilon.py` (Consolidated into T033)
- [ ] T038 Unit test for range clamping logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_estimator_clamping.py` (Consolidated into T033)

### Implementation for User Story 2

- [X] T020 Stress test script for `VirtualTactileEstimator` with noise injection in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/stress_test.py`
- [X] T021a Implement sweep generator script in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/sweep_generator.py`: Create a script that generates a CSV file `data/generated/sweep.csv` with columns `[trial_id, friction_value, torque_derivative, velocity_derivative, policy_type, success]` by simulating interactions with known friction values. **Requirement**: The script must explicitly generate test cases where object velocity $\Delta v_{object} \approx 0$ (stiction) to verify the epsilon clamping logic (FR-007) and moving average filter (FR-006). The script must accept `n_trials`, `friction_min`, and `friction_max` arguments. (DEPENDS ON T005a)
- [X] T021b Execute sweep with ground truth labels: Run `python code/sweep_generator.py --n_trials <NUM_TRIALS> --friction_min 0.0 --friction_max 2.5 --output data/generated/sweep.csv`. **Requirement**: Ensure the generated data includes the exact ground‑truth friction value for each trial to enable correlation analysis. (DEPENDS ON T021a)
- [X] T021c Calculate linear correlation between $k_{est}$ and ground‑truth friction from the sweep data in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/correlation_analysis.py`. (DEPENDS ON T021b)
- [X] T023 Verify FR-007 clamping logic via unit test `tests/unit/test_estimator_clamping.py`: assert that inputs outside the defined bounds produce clamped outputs. (DEPENDS ON T005a)
- [X] T038 Execute adaptive policy on sweep data in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/sweep_policy_eval.py`: Run the adaptive policy on the generated `sweep.csv` data to measure the **success rate improvement** required by User Story 2 Acceptance Scenario 2. Output results to `data/results/sweep_policy_results.csv`. (DEPENDS ON T021b)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - CPU‑Tractable Inference Pipeline (Priority: P3)

**Goal**: Ensure the entire experiment (data gen, training, eval, analysis) runs within 6 h and 7 GB RAM on a CPU‑only runner.

**Independent Test**: Execute full pipeline on GitHub Actions free‑tier runner with limited CPU and memory resources. Measure wall‑clock time and peak memory. Verify no CUDA errors.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T040 Unit test for `run_benchmark.py` orchestration logic in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_benchmark_orchestration.py` to verify step execution order.
- [ ] T041 Unit test for `memory_profiler.py` in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/test_memory_profiler.py` to verify peak memory capture.

### Implementation for User Story 3

- [X] T026 Optimize `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/generator.py` for low memory usage during geometry generation
- [X] T027 Optimize `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/train.py` batch sizes and simulation steps to fit 6 h limit
- [X] T028a Create `code/run_benchmark.py` orchestration script: Implement a single executable script that orchestrates the full pipeline (generating data via T013a, training via T012h, evaluating via T013e, aggregating via T014) and outputs a summary JSON. **Requirement**: This task depends on the *existence* of the code for T013a, T012h, T013e, and T014, not their prior execution. (DEPENDS ON T013a, T012h, T013e, T014)
- [X] T028b Create step wrappers in `code/run_benchmark.py`: Implement individual step wrappers for generation, training, evaluation, and aggregation. (DEPENDS ON T028a)
- [X] T028c Generate summary JSON from step results: Write final JSON `data/results/benchmark_summary.json` containing wall‑clock time, peak memory, and boolean flags `pass_sc003`, `pass_sc004`. (DEPENDS ON T028b)
- [X] T025 Implement memory profiling script `code/memory_profiler.py` using `tracemalloc` to capture peak memory usage; integrate it into `run_benchmark.py` so that peak memory is recorded. **(MANDATORY - Required for SC-004)**. (DEPENDS ON T028a)
- [X] T029 Run full end‑to‑end benchmark: Execute `python code/run_benchmark.py --output data/results/benchmark_metrics.json`. Log wall‑clock time and peak memory. (SC‑003, SC‑004 Measurement)
- [X] T029b Record benchmark results and enforce limits: Read `data/results/benchmark_metrics.json` and **FAIL the CI** if `wall_clock_time > 21600` seconds (6 h) or `peak_memory_gb > 7`. **Exit non-zero** on failure. Log the specific outcome. (DEPENDS ON T029)

**Checkpoint**: All user stories should now be independently functional.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 Documentation updates in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/docs/` and `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/README.md`: Update 'Installation', 'Usage', and 'Results' sections with CLI examples and expected outputs.
- [ ] T031 Code cleanup and refactoring of `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/estimator.py` and `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/scheduler.py`
- [ ] T032 Performance optimization for simulation loop in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/environment.py`
- [X] T033 Additional unit tests for edge cases (stiction, extreme friction, moving average filter, epsilon clamping) in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/tests/unit/`: Consolidate T036-T080 scope into a single task covering: 1) Stiction handling (epsilon clamp), 2) Extreme friction clamping, 3) Moving average filter logic (window=5), 4) Noise robustness. (Consolidated from T036-T080)
- [ ] T034 Run `quickstart.md` validation: Execute `python code/validate_quickstart.py` and verify exit code 0.
- [ ] T035 Verify `validate_citations.py` passes against all data sources
- [ ] T039 Implement reproducibility audit script in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/audit_reproducibility.py`: Generate a deterministic report of all random seeds, environment variables, and dependency hashes used in the final run to ensure exact re-runnability. (Addresses Constitution Principle I)
- [ ] T042 Implement data stream validation in `projects/PROJ-860-llmxive-follow-up-extending-dragmesh-2-p/code/stream_validator.py`: Verify that the `sweep_generator` and `evaluate` scripts process data in a streaming/chunked fashion to prevent OOM on large trial counts, logging chunk sizes to `data/results/stream_metrics.json`. (Addresses SC-003/SC-004 memory constraints)

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
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
- **CRITICAL**: All tasks must run on CPU‑only free‑tier CI (CPU, sufficient RAM, time limit). No GPU, no 8‑bit/4‑bit quantization.
- **CRITICAL**: Data loading tasks MUST fail loudly if the real source is unavailable; no synthetic fallbacks are permitted.
- **CRITICAL**: The estimator must strictly adhere to the sliding regime definition; stiction handling must be explicit via epsilon clamping, not by skipping the calculation entirely.
- **CRITICAL**: Task T013a (generation) MUST complete before T013e (evaluation) begins. The evaluation script must check for the existence of generated artifacts before proceeding.
- **RESOLVED**: T018 and T019 duplicates removed.
- **RESOLVED**: GLMM analysis added, paired t‑test removed (updated in T015f).
- **RESOLVED**: Memory profiling task added and benchmark enforcement made mandatory.
- **RESOLVED**: Consolidated excessive unit test tasks (T036-T080) into T033 for Right Granularity.
- **RESOLVED**: T005c restored with explicit manifest checksum requirements and correct key path.
- **RESOLVED**: T013a corrected to ensure 25 high-friction objects for statistical power and explicit seed.
- **RESOLVED**: T029b updated to enforce CI failure on limit breaches.
- **RESOLVED**: T038 added to validate the [deferred] improvement metric in US2.
- **RESOLVED**: T012h clarified to exclude high-friction range from training to prevent data leakage.
- **RESOLVED**: T004 strengthened to enforce global CPU-only mode.
- **RESOLVED**: T025 made mandatory for SC-004 compliance.
- **RESOLVED**: Added T039 to enforce reproducibility audit (Constitution Principle I).
- **RESOLVED**: Added T042 to enforce streaming validation for memory constraints (SC-003/SC-004).
- **RESOLVED**: T021a updated to mandate stiction test cases.
- **RESOLVED**: T016b updated to require logging of config constants.
- **RESOLVED**: Circular dependency T022/T012h removed; T022 merged into T012h.
- **RESOLVED**: T012c redefined as dry-run; dependency removed from T013e.
- **RESOLVED**: T028a dependency clarified as code existence, not execution.
- **RESOLVED**: T021a split to separate data generation from policy execution.