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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-068-evaluating-the-performance-of-different-/code/`)
- [ ] T002 Initialize Python 3.11 project with `numpy`, `scipy`, `memory-profiler`, `pytest`, `bitarray` dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (flake8/pylint) and formatting (black/isort) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Dependencies**: T014 and T015 MUST be completed before T011-T013 to ensure implementations receive correct hash functions and FPR parameters.

Examples of foundational tasks (adjust based on your project):

- [ ] T004 [P] Implement Abstract Base Class `BloomFilter` in `code/bloom_filters/base.py` defining `insert`, `contains`, and `false_positive_rate` interface
- [ ] T005 [P] Define `BenchmarkRun` data schema in `code/benchmarks/metrics.py` (fields: `dataset_size`, `fpr_target`, `implementation_type`, `peak_memory_mb`, `query_latency_ms`, `repetition_id`, `query_count`)
- [ ] T006 [P] Create synthetic data generator `code/benchmarks/generator.py` to produce log-normal distributed text samples mimicking Enron/Google distributions (validated via KS-test logic)
- [ ] T007 [P] Setup directory structure for `data/processed/` and `results/benchmarks/` with checksum verification hooks
- [ ] T008 [P] Configure `pytest` integration test framework in `tests/integration/test_benchmark_pipeline.py`
- [ ] T014 [P] [Foundational] Implement deterministic MurmurHash3 wrapper in `code/bloom_filters/hash_utils.py` ensuring identical output across all three variants; MUST be available before T011-T013.
- [ ] T015 [P] [Foundational] Implement FPR configuration logic in `code/bloom_filters/base.py` to set targets to **[deferred], [deferred], and [deferred]** (per Constitution Principle VI); MUST calculate optimal `k` and `m` parameters and assert these values are passed to and used by the implementation constructors (T011-T013).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Implement Three Bloom Filter Variants (Priority: P1) 🎯 MVP

**Goal**: Implement three Bloom filter variants (native arrays, dynamic vectors, specialized bitsets) with identical hash functions to enable performance comparison.

**Independent Test**: Can be fully tested by running insertion and query operations on each implementation with a known dataset and verifying that memory usage and latency are recorded for comparison.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for `BloomFilter` interface consistency in `tests/unit/test_bloom_filters.py`
- [ ] T010 [P] [US1] Unit test for false positive rate calculation accuracy in `tests/unit/test_bloom_filters.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `ArrayBloomFilter` using native Python lists in `code/bloom_filters/array_impl.py` (requires T014, T015)
- [ ] T012 [P] [US1] Implement `VectorBloomFilter` using `bytearray` (dynamic vector) in `code/bloom_filters/vector_impl.py` (requires T014, T015)
- [ ] T013 [P] [US1] Implement `BitsetBloomFilter` using `bitarray` library in `code/bloom_filters/bitset_impl.py` (requires T014, T015)
- [ ] T016 [US1] Add validation logic to ensure all three implementations produce identical membership results for the same query set in `code/bloom_filters/base.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Benchmark Suite Across Dataset Sizes (Priority: P2)

**Goal**: Run insertion and query benchmarks on the synthetic dataset across set sizes from 10k to 1M elements with **50 repetitions** per configuration.

**⚠️ DEPENDENCY NOTE**: Tasks T022 and T021 cannot commence until T006 (Synthetic Data Generator) is fully functional and parameterized. T019 and T020 (Metrics) must be ready before T021 (Runner) is implemented.

**Independent Test**: Can be fully tested by executing the benchmark script on a single dataset size and verifying that output files contain timing and memory measurements for all three implementations with 50 repetitions each.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Integration test for benchmark runner timeout handling in `tests/integration/test_benchmark_pipeline.py`
- [ ] T018 [P] [US2] Unit test for memory_profiler integration in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement memory measurement wrapper using `memory_profiler` in `code/benchmarks/metrics.py`
- [ ] T020 [P] [US2] Implement latency measurement wrapper with millisecond precision in `code/benchmarks/metrics.py`
- [ ] T022 [US2] Implement dataset sampling logic in `code/benchmarks/generator.py` to generate subsets from **10k, 50k, 100k, 500k, and 1M elements** (logarithmically spaced) and prepare for **[deferred] membership queries** per run.
- [ ] T035 [US2] Implement theoretical baseline calculation to record minimum memory (bits/element) and theoretical latency bounds for each implementation in `results/benchmarks/` (MUST run before T023 to populate CSVs) to satisfy SC-001 and SC-002.
- [ ] T021 [US2] Implement `BenchmarkRunner` in `code/benchmarks/runner.py` to orchestrate **50 repetitions** per configuration (dataset size × FPR × implementation); MUST execute **[deferred] queries** per run to satisfy FR-004's millisecond precision requirement.
- [ ] T023 [US2] Implement result aggregation to write CSVs to `results/benchmarks/` with headers: `size, fpr, impl, rep_id, memory_mb, latency_ms, query_count, theoretical_memory_bits`; MUST validate `query_count > 0` and abort the run if missing or zero to ensure data integrity.
- [ ] T024 [US2] Add timeout logic (30 min limit) to `code/benchmarks/runner.py` to mark runs as failed without corrupting results

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Analysis and Generate Visualizations (Priority: P3)

**Goal**: Apply Kruskal-Wallis H-test to determine statistical significance and generate memory vs. size and latency vs. size plots.

**Independent Test**: Can be fully tested by running the analysis script on sample benchmark data and verifying that output includes p-values, significance flags, and PNG/SVG plots for both memory and latency comparisons.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for Kruskal-Wallis H-test implementation in `tests/unit/test_stats.py`
- [ ] T027 [P] [US3] Unit test for plot generation logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T025 [US3] Execute cross-implementation consistency check on aggregated results to verify all three variants return identical results for the same inputs (Post-Run Validation).
- [ ] T029 [US3] Implement data aggregation logic to group results by `dataset_size` and `implementation` in `code/benchmarks/stats.py` (MUST precede T028)
- [ ] T028 [P] [US3] Implement Kruskal-Wallis H-test logic in `code/benchmarks/stats.py` using `scipy.stats.kruskal` (depends on T029)
- [ ] T030 [US3] Implement visualization generation for "Memory vs. Set Size" plot in `code/benchmarks/stats.py` (3 lines, one per impl)
- [ ] T031 [US3] Implement visualization generation for "Latency vs. Set Size" plot in `code/benchmarks/stats.py` (3 lines, one per impl)
- [ ] T032 [US3] Add logic to compute and log p-values and significance flags (α = 0.05) to `results/benchmarks/analysis_summary.json`
- [ ] T033 [US3] Implement coefficient of variation (CV) calculation to verify reproducibility (≤15% target) across repetitions; MUST calculate CV for each configuration.
- [ ] T034 [US3] Implement CV enforcement logic: if CV > 15%, **flag the configuration as 'unstable'**, **mark the run as failed**, and **trigger an automatic re-run** (up to 3 attempts) before escalating to human input.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `README.md` and `docs/`
- [ ] T037 Code cleanup and refactoring for `code/bloom_filters/`
- [ ] T038 Performance optimization for `code/benchmarks/runner.py` (ensure a sufficient number of runs fit within 6 hours)
- [ ] T039 [P] Additional unit tests for edge cases (empty dataset, max memory) in `tests/unit/`
- [ ] T040 Run `quickstart.md` validation to ensure all scripts execute correctly
- [ ] T041 Verify all [deferred] values in spec/plan are addressed or explicitly noted as research outputs

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
- **Repetition Count**: All benchmarks must run **50 repetitions** per configuration (not 5) to satisfy Plan performance goals and statistical power requirements.
- **Query Count**: Each benchmark run must execute **[deferred] membership queries** to satisfy FR-004 millisecond precision requirements.
- **FPR Values**: False Positive Rate targets are fixed at **[deferred], [deferred], and [deferred]** per Constitution Principle VI.
- **CV Enforcement**: Coefficient of Variation must be ≤15%; runs exceeding this must be flagged, failed, and retried (T034).
- **Theoretical Baselines**: Theoretical memory/latency bounds must be calculated and recorded in CSVs (T035) to satisfy SC-001/SC-002.