# Tasks: Investigating the Impact of Compiler Optimizations on LLM Inference Latency

**Input**: Design documents from `/specs/001-investigating-the-impact-of-compiler-opt/`
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

## Phase 0: Specification Alignment (Critical Prerequisites)

**Purpose**: Resolve contradictions between `spec.md` and `plan.md` immediately to ensure "Single Source of Truth" before implementation begins.

- [ ] T038 [P] [Spec] Update `spec.md` FR-004 to explicitly state "Welch's Independent Samples t-test" instead of "paired t-tests" to align with statistical validity and `plan.md`. **Action: Edit `spec.md` text immediately to replace "paired t-tests" with "Welch's Independent Samples t-test" and update the rationale to reflect independent binaries. Verify by running a diff check against the plan.md summary.**

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` by executing `mkdir -p projects/PROJ-057-investigating-the-impact-of-compiler-opt/{code/{kernels,benchmarks,analysis,utils},data/{raw,intermediates,results},tests/{unit,integration}}`
- [X] T002 Create `code/requirements.txt` containing: `numpy`, `scipy`, `matplotlib`, `pyyaml`, `pytest`, `pandas`, `pandas-stubs`
- [X] T003 Create `code/.flake8` and `code/pyproject.toml` with black formatting configuration for the compiler optimization project.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `code/benchmarks/config.py` to handle compiler flags. **Requirement: MUST implement dynamic generation of combinations from a user-supplied YAML/JSON list (e.g., `flags.yaml`). The user-supplied list MUST REPLACE the hardcoded defaults (`-O0` to `-O3`, `-Os`, `-march=native`, `-ffast-math`, `-funroll-loops`) for combinatorial generation. If no user list is provided, use the defaults. Verify by running `python code/benchmarks/config.py --generate-combinations --input flags.yaml` which outputs the full list of combinations to `data/raw/combinations.json`.**
- [ ] T005 [P] Implement deterministic synthetic tensor generator in `code/benchmarks/tensor_generator.py` using fixed seeds **[12345, 67890, 11111]** and varied distributions (Normal, Uniform) to ensure construct validity; output to `data/raw/`. **Verify by running `python code/benchmarks/tensor_generator.py --seed <SEED> --verify-hash` which generates the file, prints its SHA-256 hash, and saves the hash to `data/raw/.hashes/<SEED>.sha256`. Subsequent runs must match this hash.**
- [ ] T006 [P] Implement high-precision reference engine in `code/benchmarks/reference.py` using Python `decimal` module with arbitrary-precision arithmetic for MatMul, Softmax, and LayerNorm; output to `data/raw/`. **Verify by running `python code/benchmarks/reference.py --test --verify-hash` which generates a reference for a 2x2 matrix, prints its SHA-256 hash, and saves it to `data/raw/.hashes/ref_2x2.sha256`.**
- [X] T007 Setup logging infrastructure in `code/utils/logger.py` to record compiler versions, flag combinations, and runtime warnings (NaN detection)
- [ ] T008 [X] (Duplicate of T004 - Removed)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compile and Execute Kernel Benchmarks (Priority: P1) 🎯 MVP

**Goal**: Compile C++ kernels with varying optimization flags and execute them to measure latency.

**Independent Test**: The system can be fully tested by running a single kernel (e.g., matmul 512x512) with a specific flag set (e.g., `-O2`) and verifying that it produces a latency measurement and a valid output tensor within the 6-hour runtime budget.

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement C++ MatMul kernel in `code/kernels/matmul.cpp` (C++17, float32)
- [X] T012 [P] [US1] Implement C++ Softmax kernel in `code/kernels/softmax.cpp`
- [X] T013 [P] [US1] Implement C++ LayerNorm kernel in `code/kernels/layernorm.cpp`
- [X] T014 [US1] Implement `code/benchmarks/compile_runner.py` to orchestrate `g++`/`clang++` compilation with dynamic flag injection and SHA-256 hashing of binaries; **Verify by running `python code/benchmarks/compile_runner.py --test` which outputs a SHA-256 hash of a dummy binary**
- [X] T015 [US1] [Depends: T005] Implement `code/benchmarks/executor.py` to run binaries and measure latency using `std::chrono` (via subprocess). **Enforce a sufficient iteration count: Run a fixed number of iterations per configuration to ensure convergence and stability (Constitution Principle VII). Do NOT use adaptive stopping. Implement memory fallback: if 768x768 allocation fails, auto-downsample to 512x512, log 'Memory Pressure' with the new dimension ID, and continue execution. Only exit if the downsampled run also fails. Output results to `data/intermediates/raw_logs/{config_id}.jsonl` with the following schema: `{"config_id": "string", "kernel": "string", "compiler": "string", "flags": ["string"], "median_ms": float, "p95_ms": float, "iterations": int, "downsampled": bool, "tensor_dim": "string"}`. Verify by running `python code/benchmarks/executor.py --test` which produces a valid JSONL line.**
- [~] T017 [US1] [Depends: T015] Implement NaN detection and exclusion logic in `code/analysis/stability_check.py`; **Post-process raw logs to detect NaNs in output tensors, log specific flag configurations causing stability failures, and output `data/intermediates/filtered_stable_runs.csv` containing only valid runs. Verify by running `python code/analysis/stability_check.py --detect-nan` which produces the filtered CSV and a log of excluded runs.**

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation to ensure they FAIL initially (Red-Green-Refactor)**

- [ ] T009 [P] [US1] Add `tests/unit/test_config.py::test_validate_flags_rejects_invalid` to verify invalid flag rejection
- [ ] T010 [P] [US1] Add `tests/integration/test_compile_run.py::test_compile_and_run_matmul` to verify GCC/Clang compiler availability and execution

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Numerical Stability Drift (Priority: P2)

**Goal**: Compare optimized kernel outputs against the high-precision reference to calculate relative error and max absolute difference.

**Independent Test**: The system can be tested by running a kernel with `-ffast-math`, comparing its output to the high-precision reference, and verifying that a relative error metric is calculated and reported.

**⚠️ DEPENDENCY**: US2 tasks cannot start until US1 binaries and raw logs are generated (T011-T017 complete).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Add `tests/unit/test_stability.py::test_l2_norm_calculation` to verify L2 norm and MaxDiff calculation
- [ ] T019 [P] [US2] Add `tests/integration/test_stability_flow.py::test_compare_O3_vs_O0` to verify comparison logic against reference

### Implementation for User Story 2

- [ ] T020 [US2] [Depends: T015, T006] Implement `code/analysis/stability_check.py` to load binary outputs and reference results. **Verify that T006 reference data exists before proceeding.**
- [ ] T021 [US2] [Depends: T015] Implement L2 relative error and Maximum Absolute Difference calculation logic in `code/analysis/stability_check.py`
- [ ] T022 [US2] [Depends: T015, T021] Implement threshold flagging/exclusion logic in `code/analysis/stability_check.py`; **Mark `status` as 'unstable' if L2 error > 1e-5 or max diff > 1e-5, otherwise 'stable'. Output `data/results/stability_metrics.csv` with columns: `config_id`, `kernel_type`, `l2_error`, `max_diff`, `status`. Verify by running `python code/analysis/stability_check.py --aggregate` which produces the CSV with correct status flags.**
- [ ] T023 [US2] [Depends: T022] Aggregate results into `data/results/stability_metrics.csv` with columns: `config_id`, `kernel_type`, `l2_error`, `max_diff`, `status`. **Ensure `aggregated.csv` (generated in T031) strictly excludes rows where `status` is 'unstable'.**
- [ ] T024 [US2] [Depends: T023] Add visualization helper to plot error distribution per optimization level. **Output to `data/results/error_distribution.png`. Verify by running `python code/analysis/viz.py --plot-errors` which generates the file.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Pareto Frontier Analysis (Priority: P3)

**Goal**: Perform statistical tests on block-averaged latency distributions and generate Pareto frontier plots.

**Independent Test**: The system can be tested by feeding it a CSV of block-averaged latency and error data for two configurations and verifying that a p-value is calculated and a plot is generated.

**⚠️ DEPENDENCY**: US3 tasks cannot start until US1 and US2 data artifacts (CSVs, logs) are generated (T015, T023 complete).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Add `tests/unit/test_stats.py::test_welch_ttest_significance` to verify Welch's t-test implementation
- [ ] T026 [P] [US3] Add `tests/integration/test_viz.py::test_pareto_frontier_generation` to verify Pareto frontier generation

### Implementation for User Story 3

- [ ] T027 [US3] [Depends: T015, T023] Implement block-averaging logic for latency distributions in `code/analysis/stats.py`. **Generate `data/intermediates/block_averaged_data.csv` from raw logs and stability metrics. Verify by running `python code/analysis/stats.py --block-average` which produces the CSV.**
- [ ] T028 [US3] [Depends: T027, T038] Implement **Welch's Independent Samples t-test** logic in `code/analysis/stats.py` to compare optimization levels (p<0.05 threshold) for independent binaries (different compilers/flags); **Verify by running `python code/analysis/stats.py --t-test` which outputs p-values and significance status. Ensure T038 (Spec update) is complete (it is now in Phase 0).**
- [ ] T029 [US3] [Depends: T028] Implement null hypothesis rejection/retention logic and logging in `code/analysis/stats.py`
- [ ] T030 [US3] [Depends: T023, T029] Implement `code/analysis/viz.py` to generate `data/results/pareto_frontier_exploration.png` including **ALL configurations (stable and unstable)**. **Explicitly mark downsampled configurations with a distinct visual indicator (e.g., different color) and unstable configurations with a 'warning' style (e.g., red outline). x-axis=median_latency, y-axis=max_abs_diff. Verify by running `python code/analysis/viz.py --plot-exploration` which generates the file.**
- [ ] T031 [US3] [Depends: T023, T029] Implement `code/analysis/viz.py` to generate `data/results/pareto_frontier_final.png` strictly **excluding** configurations with error > 1e-5 (Constitution Principle VI); **Output to `data/results/pareto_frontier_final.png` and `data/results/aggregated.csv`. The `aggregated.csv` MUST strictly exclude unstable configurations. Verify by running `python code/analysis/viz.py --plot-final` which generates the file and CSV.**
- [ ] T032 [X] (Duplicate of T031 - Removed)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Implement `code/main.py` entry point to orchestrate full experiment flow (Gen → Compile → Run → Analyze → Viz)
- [ ] T034 [P] Implement `data/manifest.json` generation with SHA-256 hashes for binaries, raw logs, CSVs, and plots (Constitution Principle V)
- [ ] T035 [P] Documentation updates: Update `README.md` with benchmark usage instructions and create `docs/benchmark_guide.md`. **Verify by running `python code/main.py --help` and checking that `README.md` contains the output.**
- [ ] T036 [P] Run `quickstart.md` validation to ensure reproducibility on fresh runners. **Generate `validation_report.json` with pass/fail status for each step. Verify by checking `validation_report.json` exists and contains no failures.**
- [ ] T037 [P] Code cleanup and refactoring to ensure modularity. **Generate `refactoring_report.md` and run `flake8 --max-complexity=10`. Verify by checking `refactoring_report.md` exists and `flake8` passes.**

---

## Phase N+1: Specification & Plan Alignment (Review Resolution)

**Purpose**: Address specific inconsistencies identified between `spec.md`, `plan.md`, and `tasks.md` to ensure the "Single Source of Truth" principle is maintained.

- [X] T038 [P] [Spec] (Moved to Phase 0) Update `spec.md` FR-004 to explicitly state "Welch's Independent Samples t-test" instead of "paired t-tests" to align with statistical validity and `plan.md`.
- [ ] T039 [P] [Spec] Update `spec.md` FR-005 to explicitly define "valid configurations" as "numerically stable configurations (L2 error ≤ 1e-5)" and clarify that downsampled runs are included in exploration plots.
- [ ] T040 [P] [Plan] Update `plan.md` to replace "[deferred]" with "Fixed 1000 iterations (cap)" and correct "Python `decimal` module (-bit precision)" to "512-bit precision".
- [ ] T041 [P] [Spec] Update `spec.md` Edge Cases section to explicitly state the behavior for NaN detection: "log specific flag configuration, exclude from statistical analysis, retain in raw logs."

---

## Phase N+2: Execution Hardening & Artifact Verification

**Purpose**: Add missing tasks to ensure the execution stage can reliably detect compiler versions, validate tensor generation, and handle the full experiment lifecycle without silent failures.

- [ ] T042 [P] [US1] Implement `code/benchmarks/compiler_validator.py` to detect and report GCC/Clang versions, failing immediately if versions are <11 (GCC) or <14 (Clang) with a clear error message citing the minimum requirement.
- [ ] T043 [P] [US1] Add `tests/integration/test_tensor_generator.py::test_seed_determinism` to verify that running `tensor_generator.py` with the same seed produces byte-identical outputs across runs.
- [ ] T044 [P] [US3] Implement `code/analysis/manifest_builder.py` to automate the SHA-256 hashing of all final artifacts (binaries, logs, CSVs, plots) and write to `data/manifest.json` immediately after the experiment completes.
- [ ] T045 [P] [US3] Add `tests/integration/test_full_flow.py::test_end_to_end_reproducibility` to simulate a fresh runner environment by cleaning `data/` and re-running `main.py`, verifying that outputs match the previous run's hashes stored in `data/manifest.json`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Spec Alignment (Phase N+1)**: Can be performed in parallel with implementation but MUST be completed before final release.
- **Execution Hardening (Phase N+2)**: Can be performed in parallel with implementation but MUST be completed before final release.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (binary execution results)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 output (latency and error data)

### Within Each User Story

- Tests (if included) MUST be written to FAIL before implementation (Red-Green-Refactor)
- Models/Generators before Services/Executors
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Specification updates (T038-T041) and Execution Hardening (T042-T045) can be done in parallel with code implementation.

---

## Parallel Example: User Story 1

```bash
# Launch all kernels for User Story 1 together:
Task: "Implement C++ MatMul kernel in code/kernels/matmul.cpp"
Task: "Implement C++ Softmax kernel in code/kernels/softmax.cpp"
Task: "Implement C++ LayerNorm kernel in code/kernels/layernorm.cpp"

# Launch all tests for User Story 1 (after implementation):
Task: "Add tests/unit/test_config.py::test_validate_flags_rejects_invalid"
Task: "Add tests/integration/test_compile_run.py::test_compile_and_run_matmul"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (MatMul only, -O2 flag)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Full kernel set, all flags) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Stability metrics) → Test independently → Deploy/Demo
4. Add User Story 3 (Stats & Viz) → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Kernels & Compilation)
 - Developer B: User Story 2 (Stability Analysis)
 - Developer C: User Story 3 (Stats & Viz)
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
- **Critical Constraint**: All tasks must run on a CPU-only, multi-core, constrained RAM environment.. No GPU, no 8-bit quantization, no large model training.
- **Constitution Principle VII**: FIXED iteration count of [deferred] per configuration is mandatory. Adaptive stopping (CV ≤ 1%) is explicitly REJECTED to prevent selection bias.
- **Statistical Validity**: Welch's Independent Samples t-test is required for comparing independent binaries, overriding ambiguous Spec wording. The Spec (FR-004) has been updated in T038 (Phase 0) to match the Plan.
- **Constitution Principle VI**: Configurations with error > 1e-5 are excluded from final results (T031) but must be logged and included in exploration plots (T030) with a warning style. Downsampled runs are considered valid and must be included in T030 with a distinct marker.
- **Plan Note**: The Plan currently lists "[deferred]" for iterations. Task T015 resolves this to a cap of [deferred] (fixed). The Plan requires a manual update (T040) to reflect "Fixed [deferred] iterations".
- **Spec Note**: The Spec (FR-004) listed "paired t-test" but the Plan and statistical validity require "Welch's Independent Samples t-test". Task T038 (Phase 0) updates the Spec immediately to match the Plan.
- **Spec Note**: The Spec (FR-005) lists "all valid configurations" but does not explicitly define "valid" as "stable". Task T030 and T031 clarify this; the Spec must be updated (T039).
- **Plan Note**: The Plan lists "Python `decimal` module (-bit precision)". Task T006 resolves this to "512-bit". The Plan must be updated (T040).
- **Execution Note**: Task T042 ensures the build fails loudly if the environment does not meet compiler requirements, preventing silent execution with unsupported flags.
- **Verification Note**: Tasks T043 and T045 ensure that the synthetic data generation and full experiment flow are deterministic and reproducible on fresh runners.