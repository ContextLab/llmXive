# Tasks: Impact of Cache Line Padding on False Sharing in Concurrent Counters

**Input**: Design documents from `/specs/001-impact-of-cache-line-padding-on-false-sh/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create project directory structure: `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/` with `code/`, `data/`, `state/`, `.github/` directories. **Also create** `code/benchmark/` and `code/scripts/` subdirectories. **Verification**: Run `ls projects/PROJ-677-impact-of-cache-line-padding-on-false-sh` and verify output contains `code`, `data`, `state`, `.github`. Run `ls projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/benchmark` and `ls projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/scripts` to confirm subdirectories exist. Create `README.md`, `.gitignore` in root.
- [X] T002 [P] Initialize C++17 build system: Create `CMakeLists.txt` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/` with `cmake_minimum_required(VERSION 3.10)` and `set(CMAKE_CXX_STANDARD 17)`. Initialize Python environment: Create `requirements.txt` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/analysis/` with `pandas`, `scipy`, `matplotlib`, `pydantic`, `pyyaml`. **Verification**: Run `cmake --version` and `pip install -r requirements.txt` (dry run) to ensure no errors.
- [ ] T003 [P] Configure `.gitignore` and basic linting: Create `.gitignore` with patterns `*.o`, `*.a`, `*.so`, `*.log`, `data/raw/*`, `data/processed/*`, `__pycache__/`, `*.pyc`. Create `.clang-format` (based on LLVM style) and `.black` config. **Verification**: Run `git check-ignore -v *.o` (should match) and `clang-format --version`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 [P] Create and execute `hardware_detect.py` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/analysis/` to **detect and record** CPU model, core count, cache line size, and compiler flags. **Output**: `hardware_spec.yaml` with keys `cpu_model`, `core_count`, `cache_line_size`, `compiler_flags`, `timestamp`. **Constraint**: This script MUST NOT attempt to set CPU governor or modify system state; it is read-only detection only. **Verification**: Run `python hardware_detect.py` and verify exit code 0. Then verify `hardware_spec.yaml` exists and contains all required keys with non-empty values (e.g., `grep -q 'cpu_model' hardware_spec.yaml && grep -q 'core_count' hardware_spec.yaml && grep -q 'cache_line_size' hardware_spec.yaml`).
- [ ] T007a [P] [FR-002] Create `counter_packed.hpp` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/benchmark/`. Define `struct CounterPacked { long c1; long c2; long c3; }` with `#pragma pack(1)`. **DEPENDS_ON**: T002. **Verification**: Compile a small test file including this header and use `static_assert(sizeof(CounterPacked) == 24, "Packed size must be 24")`. Additionally, verify the presence of `#pragma pack(1)` in the source file: `grep -q '#pragma pack(1)' counter_packed.hpp`.
- [ ] T007b [P] [FR-002] Create `counter_padded.hpp` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/benchmark/`. Define `struct CounterPadded { alignas(64) long c1; alignas(64) long c2; alignas(64) long c3; }`. **DEPENDS_ON**: T002. **Verification**: Compile a small test file including this header and use `static_assert(sizeof(CounterPadded) >= 192, "Padded size must be >= 192")`.
 - **DEPENDS_ON**: T002
- [ ] T005 [P] [US1] Implement memory layout verification utility `verify_layout.cpp` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/benchmark/` to verify struct sizes and alignment of packed vs padded counters. **Verification**: Compile and run `verify_layout.cpp` and verify it prints the exact sizes (24 and >= 192) to stdout.
 - **DEPENDS_ON**: T007a, T007b
- [ ] T006 [P] Create Pydantic schemas in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/analysis/contracts/`.
 - `contracts/benchmark_run.py`: Define `BenchmarkRun` schema with fields `thread_count` (int), `configuration` (str), `iteration_count` (int), `wall_clock_time_ms` (float).
 - `contracts/aggregated_result.py`: Define `AggregatedResult` schema with fields `thread_count`, `configuration`, `mean_throughput`, `std_dev`.
 - `contracts/statistical_comparison.py`: Define `StatisticalComparison` schema with fields `thread_count` (int), `config` (str), `t_stat` (float), `p_value` (float), `cohens_d` (float), `fdr_adjusted_p` (float), `is_significant` (bool).
 - **Verification**: Create a test script that instantiates these schemas with sample data and verifies no validation errors (e.g., `python -c "from contracts.statistical_comparison import StatisticalComparison; StatisticalComparison(thread_count=1, config='packed', t_stat=0.0, p_value=0.5, cohens_d=0.1, fdr_adjusted_p=0.5, is_significant=False)"`).
 - **DEPENDS_ON**: T002
- [ ] T008 [P] Configure GitHub Actions workflow `.github/workflows/benchmark.yml` with `runs-on: ubuntu-latest`, `timeout-minutes: 360`, and explicit steps for build, run, and analysis. **Verification**: Run `yamllint.github/workflows/benchmark.yml` to ensure valid YAML and verify `timeout-minutes` is set to 360.
 - **DEPENDS_ON**: T001, T002

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Benchmark Harness Setup and Compilation (Priority: P1) 🎯 MVP

**Goal**: Set up the C++ benchmark harness and compile both counter variants (packed and padded) with optimization flags on the GitHub Actions runner.

**Independent Test**: Can be fully tested by compiling the C++ code with `g++ -O3 -march=native` and verifying the executable runs without errors on a single-threaded test run.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Unit test for `verify_layout.cpp` output validation in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/tests/unit/test_layout.cpp`. **Verification**: Run `g++ -o test_layout tests/unit/test_layout.cpp` and execute, verifying exit code 0.
 - **DEPENDS_ON**: T005, T007a, T007b
- [X] T013 [P] [US1] Integration test for build script `build.sh` success in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/tests/integration/test_build.sh`. **Verification**: Run `bash tests/integration/test_build.sh` and verify it calls `build.sh` and checks for binary existence.
 - **DEPENDS_ON**: T015

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `main.cpp` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/benchmark/` with argument parsing for thread count and configuration (packed/padded). **Verification**: Compile with `g++ -O3 -march=native` and run with `--help` to verify argument parsing.
 - **DEPENDS_ON**: T007a, T007b
- [ ] T015 [P] [US1] Implement `build.sh` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/scripts/` to compile `main.cpp`, `verify_layout.cpp`, and header files with `-O3 -march=native`. **Verification**: Run `bash build.sh` and verify `benchmark` binary exists and is executable. Check for warnings in output.
 - **DEPENDS_ON**: T002, T014, T005
- [ ] T016 [P] [US1] Implement `std::atomic<long>` usage in `main.cpp` for **ALL** threads (N=1 and N>1) to ensure atomic increments are never optimized away (FR-004). **Verification**: Run single-threaded and multi-threaded benchmarks and verify throughput > 0 and consistent across runs; inspect source to confirm `std::atomic` is used universally.
 - **DEPENDS_ON**: T014
- [ ] T017 [P] [US1] Add logging for compilation warnings and errors in `build.sh` to `build.log`. **Logic**: Redirect `stderr` and `stdout` to `build.log`. If compilation failed (exit code != 0), write "ERROR: Compilation failed" to `build.log` and exit with code 1. **Verification**: Run `build.sh` with a syntax error in `main.cpp` and verify exit code 1 and `build.log` contains "error". Additionally, when compilation succeeds, verify that `build.log` contains no lines matching the regex `warning:` or `warning` (case-insensitive).
 - **DEPENDS_ON**: T015

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multi-Threaded Experiment Execution (Priority: P2)

**Goal**: Execute the benchmark across a range of thread counts (including single and multiple threads) and both counter configurations (packed, padded), performing a large number of atomic increments per thread and recording wall-clock time over multiple repetitions.

**Independent Test**: Can be fully tested by running the benchmark binary with explicit thread-count and configuration parameters, verifying CSV output is generated with ≥5 timing samples per configuration.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for CSV output schema in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/tests/contract/test_csv_schema.py`. **Verification**: Run script against sample CSV and verify `pydantic` validation passes.
- [X] T020 [P] [US2] Integration test for `run_benchmarks.sh` generating a set of samples in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/tests/integration/test_benchmark_run.sh`. **Verification**: Run script and verify `data/raw/` contains CSV files with 5 rows per config.

### Implementation for User Story 2

- [ ] T021 [US2] Implement multi-threaded worker logic in `main.cpp` using `std::thread` and `std::atomic<long>` for [deferred] increments per thread, allocating a shared array of structs where each thread writes to a distinct element (FR-004, FR-010). **Verification**: Compile and run with 2 threads, verify no segfaults and output is generated. Additionally, verify that `CounterPacked` instances are allocated in a contiguous array where `sizeof(CounterPacked) < 64` and multiple threads write to adjacent elements, ensuring false sharing occurs. Verify that the loop in `main.cpp` executes exactly 10000000 iterations per thread.
 - **DEPENDS_ON**: T014, T007a, T007b
- [ ] T022a [P] [US2] Ensure `hardware_spec.yaml` exists before benchmark execution. **Logic**: Check if `data/hardware_spec.yaml` exists; if not, run `hardware_detect.py` (T004) to generate it. **Verification**: Run script and verify `data/hardware_spec.yaml` exists before proceeding.
 - **DEPENDS_ON**: T004
- [ ] T025 [P] [US2] Implement CPU pinning and governor setting in `run_benchmarks.sh`. **Logic**: Attempt `cpupower frequency-set -g performance`. If that fails, echo "performance" to `/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor`. **Verification**: Run script and verify `cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor` returns "performance".
 - **DEPENDS_ON**: T022a
- [ ] T022b [P] [US2] Execute benchmark binary with specific args (thread count, config) in `run_benchmarks.sh`. **Logic**: Call `./benchmark --threads N --config TYPE`. **Verification**: Run script and verify binary execution completes.
 - **DEPENDS_ON**: T015, T021, T022a, T025
- [ ] T022c [P] [US2] Validate CSV output schema and content in `run_benchmarks.sh`. **Logic**: Check that output CSV has columns `thread_count, configuration, iteration_count, wall_clock_time_ms` and no missing values. **Verification**: Run script and verify `data/raw/` contains valid CSV files.
 - **DEPENDS_ON**: T026
- [ ] T023 [P] [US2] Implement wall-clock timing logic in `main.cpp` using `std::chrono::high_resolution_clock` and output to CSV (FR-006). **Verification**: Run benchmark and verify `wall_clock_time_ms` column is populated with positive floats.
 - **DEPENDS_ON**: T021
- [ ] T024 [P] [US2] Implement CSV writer in `main.cpp` or `run_benchmarks.sh` to append rows with `thread_count, configuration, iteration_count, wall_clock_time_ms`. **Verification**: Run benchmark and parse output CSV with `pandas` to verify column names and types.
 - **DEPENDS_ON**: T023
- [ ] T026 [P] [US2] Add logic to `run_benchmarks.sh` to execute multiple runs per configuration for thread counts {1, 2, 4, 8}. If a run fails (timeout/crash), retry up to 10 times total for that config, but DO NOT escalate based on variance. **Verification**: Run script and verify `data/raw/*.csv` contains exactly 5 rows per config (excluding failed retries). Additionally, verify that `run_benchmarks.sh` contains a loop that iterates over thread counts 1, 2, 4, 8 (e.g., `grep -q 'for n in 1 2 4 8' run_benchmarks.sh`). Verify that `data/raw/*.csv` contains rows for thread_count values 1, 2, 4, and 8 for both configurations.
 - **DEPENDS_ON**: T022b
- [ ] T047 [P] [US2] Implement data integrity validation script `validate_raw_data.py` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/analysis/` to check for NaNs, missing values, and schema compliance in raw CSVs (Neutral check, no hypothesis assertion). **Verification**: Run script against sample CSV with NaNs and verify it exits with error code 1.
 - **DEPENDS_ON**: T024

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**Goal**: Perform two-sample t-tests comparing padded vs. unpadded throughput at each thread count (including N=1), compute effect sizes (Cohen's d), and generate a line plot with confidence intervals.

**Independent Test**: Can be fully tested by running the analysis script on sample CSV data and verifying the output includes p-values, effect sizes, and a generated plot file.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for Cohen's d calculation in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/tests/unit/test_statistics.py`. **Verification**: Run test and verify calculated Cohen's d matches expected value.
- [ ] T029 [P] [US3] Integration test for `run_analysis.py` generating `statistical_comparison.csv` and plot in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/tests/integration/test_analysis.py`. **Verification**: Run test and verify output files exist and contain expected data.

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `run_analysis.py` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/analysis/` to load raw CSVs and validate against Pydantic schemas. **Verification**: Run script against sample CSV and verify no validation errors.
 - **DEPENDS_ON**: T006, T022c, T047
- [ ] T031 [P] [US3] Implement aggregation logic in `run_analysis.py` to compute mean throughput and standard deviation per thread_count/configuration (FR-005). **Verification**: Run script and verify `AggregatedResult` objects are created correctly.
 - **DEPENDS_ON**: T030
- [ ] T032 [P] [US3] Implement two-sample t-test and Cohen's d calculation in `run_analysis.py` for **each thread count comparison (N ∈ {1, 2, 4, 8})**, outputting p-values for downstream correction (FR-007, FR-008, SC-005). **Verification**: Run script and verify t-statistic and p-value are calculated for N=1, 2, 4, 8.
 - **DEPENDS_ON**: T031
- [ ] T033 [P] [US3] Implement Benjamini-Hochberg FDR correction in `run_analysis.py` applied to the p-values generated by T032 for **all thread counts (N ∈ {1, 2, 4, 8})**, explicitly including N=1 in the FDR procedure (Success Criteria SC-005). **Verification**: Run script and verify FDR-adjusted p-values are calculated for N=1, 2, 4, 8.
 - **DEPENDS_ON**: T032
- [ ] T034 [P] [US3] Implement matplotlib plotting in `run_analysis.py` to generate line plot with confidence interval error bars (FR-009). **Verification**: Run script and verify `plot.png` exists and shows thread count vs throughput with error bars.
 - **DEPENDS_ON**: T033
- [ ] T035 [P] [US3] Write final `statistical_comparison.csv` to `data/processed/` as the Single Source of Truth (Plan: IV. Single Source of Truth) with columns: `thread_count`, `config`, `t_stat`, `p_value`, `cohens_d`, `fdr_adjusted_p`, `is_significant` (boolean), and `q_threshold` (0.05). **Implementation**: Implement logic where `is_significant` is set to true ONLY if `fdr_adjusted_p <= 0.05`. **Verification**: Run script and verify CSV exists and contains correct columns and data, including the `is_significant` flag derived from FDR-adjusted p-value ≤ 0.05. Verify that the `is_significant` flag is NOT derived from the raw p-value.
 - **DEPENDS_ON**: T033
- [ ] T036 [P] [US3] Update `state/artifacts/checksums.json` with hash of final artifacts (cryptographic hash) and timestamp in format `{ "file": "statistical_comparison.csv", "hash": "<hash>" }` (Plan: V. Versioning Discipline). **Verification**: Run script and verify `checksums.json` is updated with correct hash.
 - **DEPENDS_ON**: T035

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Update README.md with build instructions and usage examples. **Sections**: Build Instructions, Usage Examples, Hardware Requirements. **Verification**: Run `grep -q "g++ -O3" README.md` and verify it returns true.
- [ ] T039 [P] Generate API documentation for Python analysis scripts using `sphinx` and output to `docs/api/`. **Verification**: Run `sphinx-build` and verify `docs/api/index.html` exists.
- [ ] T040 [P] Code cleanup and refactoring of C++ and Python scripts using `clang-tidy` for C++ and `flake8` for Python. **Verification**: Run `clang-tidy` and `flake8` and verify 0 warnings/errors.
- [ ] T041 [P] Apply clang-format to all C++ source files using `.clang-format` config. **Verification**: Run `clang-format -i code/benchmark/*.cpp` and verify `git diff` shows no changes.
- [ ] T042 [P] Remove unused headers and dependencies from C++ files using `include-what-you-use`. **Verification**: Run `include-what-you-use` and verify 0 unused headers reported.
- [ ] T043 [P] Additional unit tests for edge cases (e.g., thread count = 0, thread count > core count) in `tests/unit/test_edge_cases.cpp`. **Verification**: Run tests and verify they pass or fail gracefully with clear error messages.
- [ ] T044 [P] Security hardening of build scripts: Add `set -e`, `set -u` to all shell scripts and run `shellcheck`. **Verification**: Run `shellcheck code/scripts/*.sh` and verify 0 errors.
- [ ] T045 [P] Run `quickstart.md` validation script. **Verification**: Run validation script and verify it exits with code 0.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **CRITICAL ORDERING**: T007a/T007b (Headers) MUST be implemented BEFORE T005 (Verification Utility). T005 depends on T007a/T007b.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **T015 (Build)** depends on **T014 (Main)** and **T005 (Verification)** only. It compiles files produced by T014 and T005.
 - **T014 (Main)** depends on **T007a/T007b (Headers)**.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 compilation
 - **T021 (Worker Logic)** depends on **T014 (Main)** and **T007a/T007b (Headers)**.
 - **T022a (Ensure Spec)** depends on **T004**.
 - **T022b (Execute)** depends on **T015** and **T021**.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 data generation
 - **T030 (Analysis)** depends on **T006 (Schemas)** and **Phase 4 (Data Generation: T022a-T022c, T047)**.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), EXCEPT T007a/T007b must precede T005.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for verify_layout.cpp output validation in tests/unit/test_layout.cpp" (Note: Must wait for T005 and T007a/T007b)
Task: "Integration test for build script build.sh success in tests/integration/test_build.sh" (Depends on T015)

# Launch all models for User Story 1 together:
Task: "Implement main.cpp in code/benchmark/main.cpp" (Must wait for T007a/T007b)
Task: "Implement counter_packed.hpp in code/benchmark/counter_packed.hpp" (T007a)
Task: "Implement counter_padded.hpp in code/benchmark/counter_padded.hpp" (T007b)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - **Execute T007a/T007b first** (Headers)
 - **Then Execute T005** (Verification Utility)
3. Complete Phase 3: User Story 1
 - **Execute T014** (Main)
 - **Then Execute T015** (Build)
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

1. Team completes Setup + Foundational together (respecting T007a/T007b -> T005 order)
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except explicit DEPENDS_ON)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Do NOT execute tasks marked [X] if artifacts are missing. All implementation tasks below are currently [ ] (pending) unless explicitly marked [X] for completed setup tasks.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence