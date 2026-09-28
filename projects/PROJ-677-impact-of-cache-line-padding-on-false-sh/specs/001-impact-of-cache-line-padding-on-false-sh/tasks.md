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

- [ ] T001 Create project directory structure: `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/` with `code/`, `data/`, `state/`, `.github/` directories
- [ ] T002 Initialize C++17 build system (CMake or Makefile) and Python 3.11 environment with `requirements.txt` (pandas, scipy, matplotlib, pydantic, pyyaml) in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/analysis/`
- [ ] T003 [P] Configure `.gitignore` and basic linting/formatting (clang-format for C++, black/flake8 for Python)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 [P] [FR-002] [Plan-Principle-VII] Create and execute `hardware_detect.py` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/analysis/` to detect CPU model, core count, cache line size, and set CPU governor to 'performance'; output to `hardware_spec.yaml`
- [ ] T007 [P] [FR-002] Create `counter_packed.hpp` and `counter_padded.hpp` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/benchmark/` with `#pragma pack(1)` for packed (24 bytes) and `alignas(64)` for padded (≥192 bytes)
- [ ] T005 [P] [US1] Implement memory layout verification utility `verify_layout.cpp` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/benchmark/` to verify struct sizes and alignment of packed vs padded counters
 - **DEPENDS_ON**: T007
- [ ] T006 [P] Create Pydantic schemas in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/analysis/contracts/` for `BenchmarkRun` and `AggregatedResult`
- [ ] T008 [P] Configure GitHub Actions workflow `.github/workflows/benchmark.yml` with `ubuntu-latest`, a sufficient timeout for extended execution, and steps for build, run, and analysis

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Benchmark Harness Setup and Compilation (Priority: P1) 🎯 MVP

**Goal**: Set up the C++ benchmark harness and compile both counter variants (packed and padded) with optimization flags on the GitHub Actions runner.

**Independent Test**: Can be fully tested by compiling the C++ code with `g++ -O3 -march=native` and verifying the executable runs without errors on a single-threaded test run.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Unit test for `verify_layout.cpp` output validation in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/tests/unit/test_layout.cpp`
 - **DEPENDS_ON**: T005, T007
- [X] T013 [P] [US1] Integration test for build script `build.sh` success in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/tests/integration/test_build.sh`
 - **DEPENDS_ON**: T015

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `main.cpp` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/benchmark/` with argument parsing for thread count and configuration (packed/padded)
 - **DEPENDS_ON**: T007
- [ ] T015 [P] [US1] Implement `build.sh` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/scripts/` to compile `main.cpp`, `verify_layout.cpp`, and header files with `-O3 -march=native`
 - **DEPENDS_ON**: T002, T014, T005
- [ ] T016 [P] [US1] Add single-threaded validation logic in `main.cpp` to ensure atomic increments are not optimized away (FR-004)
 - **DEPENDS_ON**: T014
- [ ] T017 [P] [US1] Add logging for compilation warnings and errors in `build.sh` and exit with code 1 on failure
 - **DEPENDS_ON**: T015

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multi-Threaded Experiment Execution (Priority: P2)

**Goal**: Execute the benchmark across a range of thread counts (including single and multiple threads) and both counter configurations (packed, padded), performing a large number of atomic increments per thread and recording wall-clock time over multiple repetitions.

**Independent Test**: Can be fully tested by running the benchmark binary with explicit thread-count and configuration parameters, verifying CSV output is generated with ≥5 timing samples per configuration.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for CSV output schema in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/tests/contract/test_csv_schema.py`
- [X] T020 [P] [US2] Integration test for `run_benchmarks.sh` generating a set of samples in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/tests/integration/test_benchmark_run.sh`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement multi-threaded worker logic in `main.cpp` using `std::thread` and `std::atomic<long>` for a large number of increments per thread, allocating a shared array of structs where each thread writes to a distinct element (FR-004, FR-010)
 - **DEPENDS_ON**: T014, T007
- [ ] T022 [P] [US2] Implement `run_benchmarks.sh` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/scripts/` to iterate thread counts and configurations, execute `hardware_detect.py` to generate `hardware_spec.yaml`, and run the benchmark <!-- ATOMIZE: requested -->
 - **DEPENDS_ON**: T015, T021, T004
- [ ] T023 [P] [US2] Implement wall-clock timing logic in `main.cpp` using `std::chrono::high_resolution_clock` and output to CSV (FR-006)
 - **DEPENDS_ON**: T021
- [ ] T024 [P] [US2] Implement CSV writer in `main.cpp` or `run_benchmarks.sh` to append rows with `thread_count, configuration, iteration_count, wall_clock_time_ms`
 - **DEPENDS_ON**: T023
- [ ] T025 [P] [US2] Implement CPU pinning and governor setting in `run_benchmarks.sh` using `cpupower` first, then fallback to direct sysfs writes (Plan: Hardware Configuration Transparency)
 - **DEPENDS_ON**: T022
- [ ] T026 [P] [US2] Add logic to `run_benchmarks.sh` to execute exactly 5 runs per configuration, escalating to 10 runs if variance (standard deviation) exceeds 10% of the mean, and exclude any incomplete runs from the CSV (do not add a 'status' column) (Edge Case: time limit)
 - **DEPENDS_ON**: T022
- [ ] T047 [P] [US2] Implement data integrity validation script `validate_raw_data.py` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/analysis/` to check for NaNs, missing values, and schema compliance in raw CSVs (Neutral check, no hypothesis assertion)
 - **DEPENDS_ON**: T024

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**Goal**: Perform two-sample t-tests comparing padded vs. unpadded throughput at each thread count, compute effect sizes (Cohen's d), and generate a line plot with confidence intervals.

**Independent Test**: Can be fully tested by running the analysis script on sample CSV data and verifying the output includes p-values, effect sizes, and a generated plot file.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for Cohen's d calculation in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/tests/unit/test_statistics.py`
- [ ] T029 [P] [US3] Integration test for `run_analysis.py` generating `statistical_comparison.csv` and plot in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `run_analysis.py` in `projects/PROJ-677-impact-of-cache-line-padding-on-false-sh/code/analysis/` to load raw CSVs and validate against Pydantic schemas
 - **DEPENDS_ON**: T006, T022, T047
- [ ] T031 [P] [US3] Implement aggregation logic in `run_analysis.py` to compute mean throughput and standard deviation per thread_count/configuration (FR-005)
 - **DEPENDS_ON**: T030
- [ ] T032 [P] [US3] Implement two-sample t-test and Cohen's d calculation in `run_analysis.py` for each thread count comparison, outputting p-values for downstream correction (FR-007, FR-008, SC-005)
 - **DEPENDS_ON**: T031
- [ ] T033 [P] [US3] Implement Benjamini-Hochberg FDR correction in `run_analysis.py` applied to the p-values generated by T032 for the 4 thread count comparisons (Success Criteria SC-005)
 - **DEPENDS_ON**: T032
- [ ] T034 [P] [US3] Implement matplotlib plotting in `run_analysis.py` to generate line plot with confidence interval error bars (FR-009)
 - **DEPENDS_ON**: T033
- [ ] T035 [P] [US3] Write final `statistical_comparison.csv` to `data/processed/` as the Single Source of Truth (Plan: IV. Single Source of Truth) with columns: thread_count, config, t_stat, p_value, cohens_d, fdr_adjusted_p
 - **DEPENDS_ON**: T033
- [ ] T036 [P] [US3] Update `state/artifacts/checksums.json` with hash of final artifacts (cryptographic hash) and timestamp in format `{ "file": "statistical_comparison.csv", "hash": "<hash>" }` (Plan: V. Versioning Discipline)
 - **DEPENDS_ON**: T035

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Update README.md with build instructions and usage examples
- [ ] T039 [P] Generate API documentation for Python analysis scripts
- [ ] T040 [P] Code cleanup and refactoring of C++ and Python scripts
- [ ] T041 [P] Apply clang-format to all C++ source files
- [ ] T042 [P] Remove unused headers and dependencies from C++ files
- [ ] T043 [P] Additional unit tests for edge cases (e.g., fewer than a standard number of cores) in `tests/unit/`
- [ ] T044 [P] Security hardening of build scripts
- [ ] T045 [P] Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **CRITICAL ORDERING**: T007 (Headers) MUST be implemented BEFORE T005 (Verification Utility). T005 depends on T007.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **T015 (Build)** depends on **T014 (Main)** and **T005 (Verification)** only. It compiles files produced by T014 and T005.
 - **T014 (Main)** depends on **T007 (Headers)**.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 compilation
 - **T021 (Worker Logic)** depends on **T014 (Main)** and **T007 (Headers)**.
 - **T022 (Run Script)** depends on **T015** and **T021**.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 data generation
 - **T030 (Analysis)** depends on **T006 (Schemas)** and **Phase 4 (Data Generation: T022-T026, T047)**.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), EXCEPT T007 must precede T005.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for verify_layout.cpp output validation in tests/unit/test_layout.cpp" (Note: Must wait for T005 and T007)
Task: "Integration test for build script build.sh success in tests/integration/test_build.sh" (Depends on T015)

# Launch all models for User Story 1 together:
Task: "Implement main.cpp in code/benchmark/main.cpp" (Must wait for T007)
Task: "Implement counter_packed.hpp in code/benchmark/counter_packed.hpp" (T007)
Task: "Implement counter_padded.hpp in code/benchmark/counter_padded.hpp" (T007)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - **Execute T007 first** (Headers)
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

1. Team completes Setup + Foundational together (respecting T007 -> T005 order)
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