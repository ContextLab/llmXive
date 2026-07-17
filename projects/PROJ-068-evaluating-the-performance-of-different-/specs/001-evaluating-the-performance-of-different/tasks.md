# Tasks: Evaluating the Performance of Different Data Structures in Implementing Bloom Filters

**Input**: Design documents from `/specs/001-bloom-filter-data-structures/`
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

- [ ] T001 [P] Create project directory structure: `projects/PROJ-068-evaluating-the-performance-of-different-/code/`, `tests/`, `data/`, `results/`. **Verification**: Run `tools/setup_verify.py` to assert existence of all required directories.
- [X] T002 [P] Initialize `requirements.txt` with pinned versions: `numpy`, `scipy`, `memory-profiler`, `pytest`, `bitarray`, `murmurhash3`
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black/isort) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Dependencies**: T014 and T015 MUST be completed before T011-T013 to ensure implementations receive correct hash functions and FPR parameters.

Examples of foundational tasks (adjust based on your project):

- [X] T004 [P] Implement Abstract Base Class `BloomFilter` in `code/bloom_filters/base.py` defining `insert`, `contains`, and `false_positive_rate` interface
- [X] T005 [P] Define `BenchmarkRun` data schema in `code/benchmarks/metrics.py` (fields: `dataset_size`, `fpr_target`, `implementation_type`, `peak_memory_mb`, `query_latency_ms`, `repetition_id`, `query_count`)
- [X] T006 [P] Create synthetic data generator `code/benchmarks/generator.py` to produce log-normal distributed text samples mimicking Enron/Google distributions (validated via KS-test logic). **Note**: Data is generated in-memory and streamed to `data/processed/` as CSVs only when needed; checksums recorded for `data/processed/*.csv` to satisfy Constitution Principle III.
- [ ] T007 [P] Setup directory structure for `data/processed/` and `results/benchmarks/` with checksum verification hooks. **Action**: Create `tools/pre-commit-checksum.py` and install as git hook: `ln -s../../tools/pre-commit-checksum.py.git/hooks/pre-commit`.
- [X] T008 [P] Configure `pytest` integration test framework in `tests/integration/test_benchmark_pipeline.py`
- [X] T014 [P] [Foundational] Implement deterministic MurmurHash3 wrapper in `code/bloom_filters/hash_utils.py` ensuring identical output across all three variants; MUST be available before T011-T013.
- [X] T015 [P] [Foundational] Implement FPR configuration logic in `code/bloom_filters/base.py` to set targets to a range of low false positive rates. (per Constitution Principle VI); MUST calculate optimal `k` and `m` parameters based on these fixed values and assert these values are passed to and used by the implementation constructors (T011-T013). Note: Logic is independent of T014 hash implementation details.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Implement Three Bloom Filter Variants (Priority: P1) 🎯 MVP

**Goal**: Implement three Bloom filter variants (native arrays, dynamic vectors, specialized bitsets) with identical hash functions to enable performance comparison.

**Independent Test**: Can be fully tested by running insertion and query operations on each implementation with a known dataset and verifying that memory usage and latency are recorded for comparison.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T009 [P] [US1] Contract test for `BloomFilter` interface consistency in `tests/unit/test_bloom_filters.py`
- [X] T010 [P] [US1] Unit test for false positive rate calculation accuracy in `tests/unit/test_bloom_filters.py`

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `ArrayBloomFilter` using native Python lists in `code/bloom_filters/array_impl.py` (requires T014, T015)
- [X] T012 [P] [US1] Implement `VectorBloomFilter` using `bytearray` (dynamic vector) in `code/bloom_filters/vector_impl.py` (requires T014, T015)
- [X] T013 [P] [US1] Implement `BitsetBloomFilter` using `bitarray` library in `code/bloom_filters/bitset_impl.py` (requires T014, T015)
- [X] T016 [US1] [P] Add validation logic to ensure all three implementations produce identical membership results for the same query set in `code/bloom_filters/base.py` (requires T011-T013)
- [X] T025 [US1] [Validation Gate] Execute cross-implementation consistency check on sample data to verify all three variants return identical results for the same inputs. **Step 0**: Verify memory budget constraint is met for all implementations. **Step 1**: Verify memory budget constraint is met for all implementations. **Step 2**: Run consistency check. **Output**: `results/benchmarks/consistency_report.json`. **Pass/Fail**: Mismatch count must be 0; raise `AssertionError` if not. **Note**: This runs BEFORE bulk benchmarking (T021) to ensure validity. (requires T016, T011-T013)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Benchmark Suite Across Dataset Sizes (Priority: P2)

**Goal**: Run insertion and query benchmarks on the synthetic dataset across set sizes from small to large scales with multiple repetitions per configuration.

**⚠️ DEPENDENCY NOTE**: Tasks T022a-T022c and T021 cannot commence until T006 (Synthetic Data Generator) is fully functional and parameterized. T019 and T020 (Metrics) must be ready before T021 (Runner) is implemented.

**Independent Test**: Can be fully tested by executing the benchmark script on a single dataset size and verifying that output files contain timing and memory measurements for all three implementations with 5 repetitions each.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Integration test for benchmark runner timeout handling in `tests/integration/test_benchmark_pipeline.py`
- [X] T018 [P] [US2] Unit test for memory_profiler integration in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement memory measurement wrapper using `memory_profiler` in `code/benchmarks/metrics.py`
- [X] T020 [P] [US2] Implement latency measurement wrapper with millisecond precision in `code/benchmarks/metrics.py`
- [X] T022a [US2] [P] Generate dataset subsets across a range of scales, from tens of thousands to millions of elements. from T006 generator and save to `data/processed/` as CSVs. **Note**: Data is generated in-memory and streamed to disk. **Dependency**: Requires T006. (requires T006)
- [X] T022b [US2] [P] Generate query set for each subset. **Note**: Query count is determined by the number of elements in the subset, not a multiplier. (requires T022a)
- [X] T022c [US2] [P] Validate query count > 0 for each generated set; raise `ValueError` if validation fails. (requires T022b)
- [X] T035 [US2] [P] Implement theoretical baseline calculation to record minimum memory (bits/element) and theoretical latency bounds for each implementation. **Output**: `results/benchmarks/theoretical_baselines.csv`. Formula: `bits = n * log2(1/p) / ln(2)^2`. Apply unit adaptation: report bits for BitsetBloomFilter, convert to bytes for ArrayBloomFilter/VectorBloomFilter based on storage unit size. **Note**: Unit adaptation logic (bits vs bytes) must be applied based on implementation type. (MUST run before T023 to populate CSVs) to satisfy SC-001 and SC-002.
- [X] T021 [US2] Implement `BenchmarkRunner` in `code/benchmarks/runner.py` to orchestrate multiple repetitions per configuration (dataset size × FPR × implementation); MUST execute membership queries per run to satisfy FR-004's millisecond precision requirement. (requires T022a)
- [X] T023 [US2] Implement result aggregation to write CSVs to `results/benchmarks/` with headers: `size, fpr, impl, rep_id, memory_mb, latency_ms, query_count, theoretical_memory_bits`; MUST validate `query_count > 0` and **raise ValueError** if missing or zero, writing error details to `results/benchmarks/errors.log`. **Note**: This task runs after T035 to ensure theoretical baselines are available. (requires T021, T035)
- [X] T024 [US2] Add timeout logic to `code/benchmarks/runner.py` to mark runs as failed without corrupting results.. **Action**: Use `threading.Timer` to enforce a hardcoded constant `TIMEOUT_MINUTES = 1800` in runner.py. Raise `TimeoutError` if the 30-minute limit is exceeded; log the failure as "Timeout: Run exceeded 30 minutes" to the run log.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Analysis and Generate Visualizations (Priority: P3)

**Goal**: Apply Kruskal-Wallis H-test to determine statistical significance and generate memory vs. size and latency vs. size plots.

**Independent Test**: Can be fully tested by running the analysis script on sample benchmark data and verifying that output includes p-values, significance flags, and PNG/SVG plots for both memory and latency comparisons.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for Kruskal-Wallis H-test implementation in `tests/unit/test_stats.py`
- [X] T027 [P] [US3] Unit test for plot generation logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [X] T029a [US3] [P] Implement data grouping function in `code/benchmarks/stats.py` to group results by `dataset_size` and `implementation`.
- [X] T029b [US3] [P] Implement data serialization for stats input in `code/benchmarks/stats.py` (requires T029a).
- [X] T028 [P] [US3] Implement Kruskal-Wallis H-test logic in `code/benchmarks/stats.py` using `scipy.stats.kruskal` (depends on T029a, T029b).
- [X] T030 [US3] Implement visualization generation for "Memory vs. Set Size" plot in `code/benchmarks/stats.py` (one line per implementation) using FPR targets **0.01, 0.05, 0.10**.
- [X] T031 [US3] Implement visualization generation for "Latency vs. Set Size" plot in `code/benchmarks/stats.py` (3 lines, one per impl).
- [X] T032 [US3] Add logic to compute and log p-values and significance flags (α = 0.05) to `results/benchmarks/analysis_summary.json`.
- [X] T042 [US3] [P] Implement coefficient of variation (CV) calculation to verify reproducibility (≤15% target) across repetitions; MUST calculate CV for each configuration.
- [X] T043 [US3] Implement CV enforcement logic: if CV > 15%, **flag the configuration as 'UNSTABLE'** (add column `status` with value 'UNSTABLE' to CSV), **log a warning** with format "Config {size}/{fpr}/{impl} is UNSTABLE (CV={cv})", and **record the failure status** in the results CSV. DO NOT implement automatic re-run loops.
- [X] T061 [US3] [P] Implement project-level aggregation logic to verify SC-004: aggregate all configuration CVs, determine if all are ≤15%, and set project status to 'PASS' or 'FAIL'. Output: `results/benchmarks/project_status.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T050 [P] Update `README.md` with installation instructions, usage examples, and benchmark configuration details (FPRs at representative low thresholds; 5 reps; sizes k-1M).
- [X] T051 [P] Generate API documentation for `code/bloom_filters/` and `code/benchmarks/` using Sphinx or similar.
- [X] T052 [P] Apply `black` formatting to all Python files in `code/` and `tests/`.
- [X] T053 [P] Remove unused imports and variables from all Python files in `code/` and `tests/`.
- [X] T054 [P] Implement multiprocessing in `code/benchmarks/runner.py` to parallelize repetitions and fit within 6-hour budget.
- [X] T055 [P] Implement caching for hash computations in `code/bloom_filters/hash_utils.py` to optimize performance.
- [X] T056 [P] Run quickstart.md validation. **Action**: Assert `quickstart.md` exists, then run `pytest --quickstart-validation`.
- [X] T057 [P] Verify all specific benchmark parameters (FPRs at representative low thresholds, sizes 10k-1M, query counts) are hardcoded or configurable, no `[deferred]` placeholders remain.
- [X] T058 [P] [Review Fix: Data Integrity] Add explicit `fail_loudly` logic in `code/benchmarks/generator.py` to raise `FileNotFoundError` if synthetic distribution parameters cannot be validated, preventing silent fallback to random noise.
- [X] T059 [P] [Review Fix: Reproducibility] Add a deterministic random seed configuration task in `code/benchmarks/runner.py` ensuring all 5 repetitions use unique but reproducible seeds derived from a master seed.
- [X] T060 [P] [Review Fix: Theoretical Bounds] Add unit tests for the theoretical memory calculation formulas in T035 to ensure the `log2` and `ln` conversions are mathematically correct before benchmarking.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Critical**: T014 (Hash) and T015 (FPR Config) MUST be completed before Phase 3 (Implementations) can begin.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 implementations to benchmark
 - **Critical**: T022a-T022c and T021 depend on T006 (Data Generator) being fully functional.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 results to analyze

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for BloomFilter interface in tests/unit/test_bloom_filters.py"
Task: "Unit test for false positive rate calculation in tests/unit/test_bloom_filters.py"

# Launch all implementations for User Story 1 together:
Task: "Implement ArrayBloomFilter in code/bloom_filters/array_impl.py"
Task: "Implement VectorBloomFilter in code/bloom_filters/vector_impl.py"
Task: "Implement BitsetBloomFilter in code/bloom_filters/bitset_impl.py"
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
- **Data Integrity**: All benchmark data must be generated via the synthetic generator (T006) to comply with "No invented URLs" rule while maintaining statistical validity. Data is generated in-memory and streamed to disk as CSVs only when needed.
- **Compute Constraints**: All implementations must run on CPU-only; no GPU/CUDA dependencies allowed.
- **Repetition Count**: All benchmarks must run **multiple** repetitions per configuration (per Constitution Principle VI) to satisfy statistical power requirements within time limits.
- **Query Count**: Each benchmark run must execute membership queries per run to satisfy FR-004 millisecond precision requirements without unverified scope expansion.
- **FPR Values**: False Positive Rate targets are fixed at representative low, moderate, and high thresholds per Constitution Principle VI.
- **CV Enforcement**: Coefficient of Variation must be ≤15%; runs exceeding this must be flagged and logged as 'UNSTABLE' (T043), NOT retried automatically.
- **Project-Level Reproducibility**: T061 aggregates CVs to determine project-level PASS/FAIL status as required by SC-004.
- **Theoretical Baselines**: Theoretical memory/latency bounds must be calculated using explicit formulas (T035) to satisfy SC-001/SC-002. Output: `results/benchmarks/theoretical_baselines.csv`. Unit adaptation (bits vs bytes) is required.
- **Review Resolution**: Tasks T058, T059, and T060 address specific reviewer concerns regarding data integrity, reproducibility seeds, and theoretical bound validation.
- **Task Granularity**: T022 split into T022a (generate), T022b (query), T022c (validate). T029 split into T029a (group), T029b (serialize).
- **Consistency Check**: T025 moved to Phase 3 to run BEFORE bulk benchmarking to ensure implementation validity. T025 is a validation gate, not parallel.
- **Dependency Clarity**: T022a depends on T006 only. T021 depends on T022a. T023 depends on T021 and T035.