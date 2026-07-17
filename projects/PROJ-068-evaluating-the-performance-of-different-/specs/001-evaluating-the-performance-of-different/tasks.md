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

- [ ] T001 Create project directory structure: `projects/PROJ-068-evaluating-the-performance-of-different-/code/`, `tests/`, `data/`, `results/`. **Verification**: Run `tools/setup_verify.py` to assert existence of all required directories.
- [ ] T002 [P] Initialize `requirements.txt` with pinned versions: `numpy`, `scipy`, `memory-profiler`, `pytest`, `bitarray`, `mmh3`.
- [ ] T003 [P] Configure linting (flake8/pylint) and formatting (black/isort) tools in `pyproject.toml`
- [ ] T007 [P] Setup directory structure for `data/processed/` and `results/benchmarks/` with checksum verification hooks. **Action**: Create `tools/pre-commit-checksum.py` and install as git hook: `ln -s../../tools/pre-commit-checksum.py.git/hooks/pre-commit`. (Requires T001).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Dependencies**: T014 and T015 MUST be completed before T011-T013 to ensure implementations receive correct hash functions and FPR parameters.

Examples of foundational tasks (adjust based on your plan):

- [ ] T004 [P] Implement Abstract Base Class `BloomFilter` in `code/bloom_filters/base.py` defining `insert`, `contains`, and `false_positive_rate` interface
- [ ] T005 [P] Define `BenchmarkRun` data schema in `code/benchmarks/metrics.py` (fields: `dataset_size`, `fpr_target`, `implementation_type`, `peak_memory_mb`, `query_latency_ms`, `repetition_id`, `query_count`)
- [ ] T006 [P] Create synthetic data generator `code/benchmarks/generator.py` to produce log-normal distributed text samples mimicking Enron/Google distributions. **Parameters**: mu=2.5, sigma=1.2. **Validation**: KS-test p-value > 0.05. **Action**: Generate data in-memory, stream to `data/processed/` as CSVs, and record SHA-256 checksums to `data/checksums.manifest`. (Requires T001, T007).
- [ ] T008 [P] Configure `pytest` integration test framework in `tests/integration/test_benchmark_pipeline.py`
- [ ] T014 [P] [Foundational] Implement deterministic MurmurHash3 wrapper in `code/bloom_filters/hash_utils.py` ensuring identical output across all three variants; MUST be available before T011-T013.
- [ ] T015 [P] [Foundational] Implement FPR configuration logic in `code/bloom_filters/base.py` to set targets at low, medium, and high thresholds for each implementation variant (See US-1). **Note**: The spec defines deferred values; these are implemented with concrete values as a temporary workaround until the spec is updated.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Implement Three Bloom Filter Variants (Priority: P1) 🎯 MVP

**Goal**: Implement three Bloom filter variants (native arrays, dynamic vectors, specialized bitsets) with identical hash functions to enable performance comparison.

**Independent Test**: Can be fully tested by running insertion and query operations on each implementation with a known dataset and verifying that memory usage and latency are recorded for comparison.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T009 [P] [US1] Contract test for `BloomFilter` interface consistency in `tests/unit/test_bloom_filters.py`
- [ ] T010 [P] [US1] Unit test for false positive rate calculation accuracy in `tests/unit/test_bloom_filters.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `ArrayBloomFilter` using native Python lists in `code/bloom_filters/array_impl.py` (requires T014, T015)
- [ ] T012 [P] [US1] Implement `VectorBloomFilter` using `bytearray` (dynamic vector) in `code/bloom_filters/vector_impl.py` (requires T014, T015)
- [ ] T013 [P] [US1] Implement `BitsetBloomFilter` using `bitarray` library in `code/bloom_filters/bitset_impl.py` (requires T014, T015)
- [ ] T016 [US1] [Validation] Add validation logic to ensure all three implementations produce identical membership results for the same query set in `code/bloom_filters/base.py`. **Note**: This task depends on T011-T013 completion and CANNOT run in parallel with them. (requires T011-T013)
- [ ] T025 [US1] [Validation Gate] Execute cross-implementation consistency check on sample data to verify all three implementations return identical results for the same inputs. **Step 0**: Verify memory budget constraint is met for all implementations. **Step 1**: Run consistency check. **Output**: `results/benchmarks/consistency_report.json`. **Pass/Fail**: Mismatch count must be 0; raise `AssertionError` if not. **Note**: This runs BEFORE bulk benchmarking (T021) to ensure validity. (requires T016, T011-T013)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Benchmark Suite Across Dataset Sizes (Priority: P2)

**Goal**: Run insertion and query benchmarks on the synthetic dataset across set sizes from small to large scales with multiple repetitions per configuration.

**⚠️ DEPENDENCY NOTE**: Tasks T021 cannot commence until T014-T015 are completed.

**Independent Test**: Can be fully tested by executing the benchmark script on a single dataset size and verifying that output files contain timing and memory measurements for all three implementations with multiple repetitions each.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Integration test for benchmark runner timeout handling in `tests/integration/test_benchmark_pipeline.py`
- [ ] T018 [P] [US2] Unit test for memory_profiler integration in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement memory measurement wrapper using `memory_profiler` in `code/benchmarks/metrics.py`
- [ ] T020 [P] [US2] Implement latency measurement wrapper with millisecond precision in `code/benchmarks/metrics.py`
- [ ] T021 [US2] Implement `BenchmarkRunner` in `code/benchmarks/runner.py` to orchestrate multiple repetitions per configuration (dataset size × FPR × implementation). MUST execute membership queries per run to satisfy FR-004's millisecond precision requirement. 
- [ ] T022a [US2] [P] Generate dataset subsets across multiple logarithmically spaced dataset sizes ([deferred], [deferred], [deferred], [deferred] elements) using the generator defined in T006 (mu=2.5, sigma=1.2). **Action**: Generate data in-memory, stream to `data/processed/` as CSVs, and record SHA-256 checksums to `data/checksums.manifest`. **Validation**: Verify count matches target for each size. (Requires T006).
- [ ] T023 [US2] Implement result aggregation to write CSVs to `results/benchmarks/` with headers: `size, fpr, impl, rep_id, memory_mb, latency_ms, query_count`. MUST validate `query_count > 0` and raise ValueError if missing or zero, writing error details to `results/benchmarks/errors.log`.
- [ ] T035a [US2] [P] Implement theoretical memory baseline calculation in `code/benchmarks/stats.py` to record minimum memory (bits/element) for each implementation type. **Output**: `results/benchmarks/theoretical_memory.csv`. **Note**: MUST complete before T021. Unit adaptation logic (bits vs bytes) is applied based on implementation type to satisfy SC-001. (Requires T006, T022a).
- [ ] T035b [US2] [P] Implement theoretical latency baseline calculation in `code/benchmarks/stats.py` to record theoretical lower bound for query latency. **Output**: `results/benchmarks/theoretical_latency.csv`. **Note**: MUST complete before T021. (Requires T006, T022a).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Analysis and Generate Visualizations (Priority: P3)

**Goal**: Apply Kruskal-Wallis H-test to determine statistical significance and generate memory vs. size and latency vs. size plots.

**Independent Test**: Can be fully tested by running the analysis script on sample benchmark data and verifying that output includes p-values, significance flags, and PNG/SVG plots for both memory and latency comparisons.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for Kruskal-Wallis H-test implementation in `tests/unit/test_stats.py`
- [ ] T027 [P] [US3] Unit test for plot generation logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement Kruskal-Wallis H-test logic in `code/benchmarks/stats.py` using `scipy.stats.kruskal`.
- [ ] T029 [US3] Prepare benchmark data for statistical analysis in `code/benchmarks/stats.py`: group results by `dataset_size` and `implementation_type`, serialize for input, and compute CV. **Note**: This task replaces split tasks T029a/T029b and CANNOT run in parallel with data generation (T022a). (Requires T021, T023).
- [ ] T030 [US3] Implement visualization generation for "Memory vs. Set Size" plot in `code/benchmarks/stats.py` (one line per implementation).
- [ ] T031 [US3] Implement visualization generation for "Latency vs. Set Size" plot in `code/benchmarks/stats.py` (three lines, one per impl).
- [ ] T032 [US3] Add logic to compute and log p-values and significance flags (α = 0.05) to `results/benchmarks/analysis_summary.json`.
- [ ] T042 [P] Implement coefficient of variation (CV) calculation to verify reproducibility (≤15% target) across repetitions.
- [ ] T043 [P][US3] Calculate CV for each configuration and flag unstable configurations: If the CV exceeds a predefined threshold, add a 'UNSTABLE' status to the CSV., log a warning with format "Config {size}/{fpr}/{impl} is UNSTABLE (CV={cv})", and record the failure status.
- [ ] T061 [US3] Implement project-level aggregation logic to verify SC-004: aggregate all configuration CVs, check if ALL configurations are ≤15%, and raise a RuntimeError if any configuration exceeds this threshold. **Note**: This task depends on T043 completion and CANNOT run in parallel with it. (Requires T043).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050 [P] Update `README.md` with installation instructions, usage examples, and benchmark configuration details (FPRs at low, moderate, and high thresholds; 5 reps; sizes kM).
- [ ] T051 [P] Generate API documentation for `code/bloom_filters/` and `code/benchmarks/` using Sphinx or similar.
- [ ] T052 [P] Apply `black` formatting to all Python files in `code/` and `tests/`.
- [ ] T053 [P] Remove unused imports and variables from all Python files in `code/` and `tests/`.
- [ ] T054 [P] Implement multiprocessing in `code/benchmarks/runner.py` to parallelize repetitions and fit within 6-hour budget.
- [ ] T055 [P] Implement caching for hash computations in `code/bloom_filters/hash_utils.py` to optimize performance.
- [ ] T056 [P] Run quickstart.md validation. **Action**: Assert `quickstart.md` exists, then run `pytest --quickstart-validation`.
- [ ] T057 [P] Verify all specific benchmark parameters (FPRs at low thresholds, sizes ranging from small to large scales, query counts) are hardcoded or configurable, no `[deferred]` placeholders remain.
- [ ] T058 [P] [Review Fix: Data Integrity] Add explicit `fail_loudly` logic in `code/benchmarks/generator.py` to raise `FileNotFoundError` if synthetic distribution parameters cannot be validated, preventing silent fallback to random noise.
- [ ] T059 [P] [Review Fix: Reproducibility] Add a deterministic random seed configuration task in `code/benchmarks/runner.py` ensuring All repetitions use unique but reproducible seeds derived from a master seed using `secrets.SystemRandom` and a fixed integer master seed.
- [ ] T060 [P] [Review Fix: Theoretical Bounds] Add unit tests for the theoretical memory calculation formulas to ensure the calculations are mathematically correct before benchmarking.

---

## Dependencies & Execution Order

(Same as original document)

## Parallel Example: User Story 1

(Same as original document)

## Implementation Strategy

(Same as original document)

## Notes

(Updated with notes reflecting changes and resolutions of concerns)

# Constitution (FR-030)

(Same as original document)