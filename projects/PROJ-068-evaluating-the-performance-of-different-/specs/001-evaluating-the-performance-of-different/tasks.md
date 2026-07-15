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

- [ ] T001 [P] Create project directory structure: `projects/PROJ-068-evaluating-the-performance-of-different-/code/`, `tests/`, `data/`, `results/`
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
- [X] T006 [P] Create synthetic data generator `code/benchmarks/generator.py` to produce log-normal distributed text samples mimicking Enron/Google distributions (validated via KS-test logic)
- [ ] T007 [P] Setup directory structure for `data/processed/` and `results/benchmarks/` with checksum verification hooks
- [X] T008 [P] Configure `pytest` integration test framework in `tests/integration/test_benchmark_pipeline.py`
- [X] T014 [P] [Foundational] Implement deterministic MurmurHash3 wrapper in `code/bloom_filters/hash_utils.py` ensuring identical output across all three variants; MUST be available before T011-T013.
- [X] T015 [P] [Foundational] Implement FPR configuration logic in `code/bloom_filters/base.py` to set targets to **0.01, 0.05, and 0.10** (per Constitution Principle VI); MUST calculate optimal `k` and `m` parameters based on these fixed values and assert these values are passed to and used by the implementation constructors (T011-T013). Note: Logic is independent of T014 hash implementation details.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Implement Three Bloom Filter Variants (Priority: P1) 🎯 MVP

**Goal**: Implement three Bloom filter variants (native arrays, dynamic vectors, specialized bitsets) with identical hash functions to enable performance comparison.

**Independent Test**: Can be fully tested by running insertion and query operations on each implementation with a known dataset and verifying that memory usage and latency are recorded for comparison.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for `BloomFilter` interface consistency in `tests/unit/test_bloom_filters.py`
- [X] T010 [P] [US1] Unit test for false positive rate calculation accuracy in `tests/unit/test_bloom_filters.py`

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `ArrayBloomFilter` using native Python lists in `code/bloom_filters/array_impl.py` (requires T014, T015)
- [X] T012 [P] [US1] Implement `VectorBloomFilter` using `bytearray` (dynamic vector) in `code/bloom_filters/vector_impl.py` (requires T014, T015)
- [X] T013 [P] [US1] Implement `BitsetBloomFilter` using `bitarray` library in `code/bloom_filters/bitset_impl.py` (requires T014, T015)
- [X] T016 [US1] [P] Add validation logic to ensure all three implementations produce identical membership results for the same query set in `code/bloom_filters/base.py` (requires T011-T013)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Benchmark Suite Across Dataset Sizes (Priority: P2)

**Goal**: Run insertion and query benchmarks on the synthetic dataset across set sizes from 10k to 1M elements with **5 repetitions** per configuration.

**⚠️ DEPENDENCY NOTE**: Tasks T022 and T021 cannot commence until T006 (Synthetic Data Generator) is fully functional and parameterized. T019 and T020 (Metrics) must be ready before T021 (Runner) is implemented.

**Independent Test**: Can be fully tested by executing the benchmark script on a single dataset size and verifying that output files contain timing and memory measurements for all three implementations with 5 repetitions each.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Integration test for benchmark runner timeout handling in `tests/integration/test_benchmark_pipeline.py`
- [X] T018 [P] [US2] Unit test for memory_profiler integration in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement memory measurement wrapper using `memory_profiler` in `code/benchmarks/metrics.py`
- [X] T020 [P] [US2] Implement latency measurement wrapper with millisecond precision in `code/benchmarks/metrics.py`
- [X] T022 [US2] [P] Implement dataset sampling logic in `code/benchmarks/generator.py` to generate subsets from **10k, 50k, 100k, 500k, and 1M elements** (logarithmically spaced) and prepare for **10x dataset size (min 10k)** membership queries per run (requires T006).
- [ ] T035 [US2] [P] Implement theoretical baseline calculation to record minimum memory (bits/element) and theoretical latency bounds for each implementation in `results/benchmarks/` (requires T021). Formula: `bits = n * log2(1/p) / ln(2)^2`. For arrays/vectors, calculate theoretical bits per element; for bitsets, calculate actual bits used. (MUST run before T023 to populate CSVs) to satisfy SC-001 and SC-002.
- [X] T021 [US2] Implement `BenchmarkRunner` in `code/benchmarks/runner.py` to orchestrate **5 repetitions** per configuration (dataset size × FPR × implementation); MUST execute **10x dataset size (min 10k)** queries per run to satisfy FR-004's millisecond precision requirement.
- [ ] T023 [US2] Implement result aggregation to write CSVs to `results/benchmarks/` with headers: `size, fpr, impl, rep_id, memory_mb, latency_ms, query_count, theoretical_memory_bits`; MUST validate `query_count > 0` and abort the run if missing or zero to ensure data integrity (requires T035).
- [X] T024 [US2] Add timeout logic (min limit) to `code/benchmarks/runner.py` to mark runs as failed without corrupting results

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Analysis and Generate Visualizations (Priority: P3)

**Goal**: Apply Kruskal-Wallis H-test to determine statistical significance and generate memory vs. size and latency vs. size plots.

**Independent Test**: Can be fully tested by running the analysis script on sample benchmark data and verifying that output includes p-values, significance flags, and PNG/SVG plots for both memory and latency comparisons.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for Kruskal-Wallis H-test implementation in `tests/unit/test_stats.py`
- [ ] T027 [P] [US3] Unit test for plot generation logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T025 [US3] Execute cross-implementation consistency check on aggregated results to verify all three variants return identical results for the same inputs (Post-Run Validation).
- [ ] T029 [US3] Implement data aggregation logic to group results by `dataset_size` and `implementation` in `code/benchmarks/stats.py` (MUST precede T028)
- [ ] T028 [P] [US3] Implement Kruskal-Wallis H-test logic in `code/benchmarks/stats.py` using `scipy.stats.kruskal` (depends on T029)
- [ ] T030 [US3] Implement visualization generation for "Memory vs. Set Size" plot in `code/benchmarks/stats.py` (3 lines, one per impl) using FPR targets **0.01, 0.05, 0.10**.
- [ ] T031 [US3] Implement visualization generation for "Latency vs. Set Size" plot in `code/benchmarks/stats.py` (3 lines, one per impl)
- [ ] T032 [US3] Add logic to compute and log p-values and significance flags (α = 0.05) to `results/benchmarks/analysis_summary.json`
- [ ] T042 [US3] [P] Implement coefficient of variation (CV) calculation to verify reproducibility (≤15% target) across repetitions; MUST calculate CV for each configuration.
- [ ] T043 [US3] Implement CV enforcement logic: if CV > 15%, **flag the configuration as 'unstable'**, **log a warning**, and **record the failure status** in the results CSV. DO NOT implement automatic re-run loops.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050 [P] Update `README.md` with installation instructions, usage examples, and benchmark configuration details ([deferred], [deferred], [deferred] FPR; 5 reps).
- [ ] T051 [P] Generate API documentation for `code/bloom_filters/` and `code/benchmarks/` using Sphinx or similar.
- [ ] T052 [P] Apply `black` formatting to all Python files in `code/` and `tests/`.
- [ ] T053 [P] Remove unused imports and variables from all Python files in `code/` and `tests/`.
- [ ] T054 [P] Implement multiprocessing in `code/benchmarks/runner.py` to parallelize repetitions and fit within 6-hour budget.
- [ ] T055 [P] Implement caching for hash computations in `code/bloom_filters/hash_utils.py` to optimize performance.
- [ ] T056 [P] Run `quickstart.md` validation to ensure all scripts execute correctly.
- [ ] T057 [P] Verify all specific benchmark parameters (FPRs, sizes, query counts) are hardcoded or configurable, no `[deferred]` placeholders remain.

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
 - **Critical**: T022 and T021 depend on T006 (Data Generator) being fully functional.
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
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
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
- **Data Integrity**: All benchmark data must be generated via the synthetic generator (T006) to comply with "No invented URLs" rule while maintaining statistical validity.
- **Compute Constraints**: All implementations must run on CPU-only; no GPU/CUDA dependencies allowed.
- **Repetition Count**: All benchmarks must run **5 repetitions** per configuration (per Constitution Principle VI) to satisfy statistical power requirements within time limits.
- **Query Count**: Each benchmark run must execute **10x dataset size (min 10k)** membership queries to satisfy FR-004 millisecond precision requirements.
- **FPR Values**: False Positive Rate targets are fixed at **0.01, 0.05, and 0.10** per Constitution Principle VI.
- **CV Enforcement**: Coefficient of Variation must be ≤15%; runs exceeding this must be flagged and logged as unstable (T043), NOT retried automatically.
- **Theoretical Baselines**: Theoretical memory/latency bounds must be calculated using explicit formulas (T035) to satisfy SC-001/SC-002.
- **Plan Mismatch Note**: The Plan artifact (plan.md) currently states "50 repetitions". This tasks.md file aligns with Constitution Principle VI (5 repetitions). The Plan artifact requires a separate update to resolve this contradiction.