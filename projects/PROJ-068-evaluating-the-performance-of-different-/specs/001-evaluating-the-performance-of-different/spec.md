# Feature Specification: Evaluating the Performance of Different Data Structures in Implementing Bloom Filters

**Feature Branch**: `001-bloom-filter-data-structures`  
**Created**: 2025-01-15  
**Status**: Draft  
**Input**: User description: "How do underlying data structures (native arrays, dynamic vectors, and specialized bitsets) affect the memory overhead and operation latency of Bloom filters across varying dataset sizes?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Implement Three Bloom Filter Variants (Priority: P1)

As a researcher, I need to implement three Bloom filter variants using native arrays, dynamic vectors, and specialized bitsets so that I can compare their performance characteristics under controlled conditions.

**Why this priority**: This is the foundational capability without which no benchmarking or analysis can occur. All subsequent testing depends on having working implementations.

**Independent Test**: Can be fully tested by running insertion and query operations on each implementation with a known dataset and verifying that false positive rates match theoretical expectations within ±1% tolerance.

**Acceptance Scenarios**:

1. **Given** a Bloom filter implementation is instantiated with [deferred] elements and [deferred] false positive rate target, **When** [deferred] unique strings are inserted and [deferred] membership queries are executed, **Then** at least 99% of queries for inserted elements return true positives.
2. **Given** a Bloom filter with known hash function parameters, **When** [deferred] non-member strings are queried, **Then** no more than 11% of queries return false positives (1% target + 1% tolerance margin).
3. **Given** the three implementations are configured with identical hash functions and memory budgets, **When** the same [deferred]-element dataset is processed, **Then** all three implementations produce identical membership results for the same query set.

---

### User Story 2 - Execute Benchmark Suite Across Dataset Sizes (Priority: P2)

As a researcher, I need to run insertion and query benchmarks across set sizes from [deferred] to [deferred] elements with 5 repetitions per configuration so that I can measure performance trends and account for system noise.

**Why this priority**: This enables the core research question to be answered by generating the empirical data needed for comparison. Without systematic benchmarking, no performance conclusions can be drawn.

**Independent Test**: Can be fully tested by executing the benchmark script on a single dataset size (e.g., [deferred] elements) and verifying that output files contain timing and memory measurements for all three implementations with 5 repetitions each.

**Acceptance Scenarios**:

1. **Given** a dataset size of [deferred] elements is specified, **When** the benchmark script executes, **Then** memory_profiler or OS-level tools record peak memory usage for each of the three implementations across 5 independent runs.
2. **Given** the benchmark completes, **When** the results are aggregated, **Then** wall-clock time for [deferred] membership queries is recorded with at least 3 decimal places of precision (milliseconds).
3. **Given** any single benchmark run exceeds 30 minutes, **When** the timeout threshold is reached, **Then** the run is marked as failed and logged without corrupting results from other repetitions.

---

### User Story 3 - Perform Statistical Analysis and Generate Visualizations (Priority: P3)

As a researcher, I need to apply Kruskal-Wallis H-test to determine statistical significance and generate memory vs. size and latency vs. size plots so that I can document findings in a reproducible format.

**Why this priority**: This delivers the final research output and enables validation of the hypothesis. Without statistical analysis, observed differences remain anecdotal.

**Independent Test**: Can be fully tested by running the analysis script on sample benchmark data and verifying that output includes p-values, significance flags, and PNG/SVG plots for both memory and latency comparisons.

**Acceptance Scenarios**:

1. **Given** benchmark results from 5 repetitions across 10 dataset sizes, **When** the Kruskal-Wallis H-test is applied, **Then** a p-value is computed for each performance metric (memory, latency) comparing the three implementations.
2. **Given** p < 0.05 for any metric, **When** the results are documented, **Then** the finding is explicitly labeled as "statistically significant" with the exact p-value recorded to 4 decimal places.
3. **Given** the analysis completes, **When** visualizations are generated, **Then** at least 2 plots are produced: one showing memory usage vs. set size and one showing query latency vs. set size, each with 3 lines (one per implementation).

---

### Edge Cases

- What happens when a dataset size exceeds available RAM (e.g., [deferred] elements with low false positive rate requiring large bitset)?
- How does the system handle dataset download failures (e.g., Google 10000 English words URL becomes unavailable)?
- What occurs when false positive rate targets conflict with memory constraints (e.g., [deferred] FPR with [deferred] elements exceeds 14GB disk)?
- How are hash function collisions detected and reported during implementation validation?
- What happens when benchmark runs show high variance (>20% coefficient of variation) across the 5 repetitions?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST implement three Bloom filter variants using native arrays, dynamic vectors, and specialized bitsets with identical hash functions (See US-1)
- **FR-002**: System MUST configure false positive rate targets at [deferred], [deferred], and [deferred] for each implementation variant (See US-1)
- **FR-003**: System MUST measure peak memory usage via memory_profiler or OS-level tools during all benchmark executions (See US-2)
- **FR-004**: System MUST record wall-clock time for [deferred] membership queries per dataset size with millisecond precision (See US-2)
- **FR-005**: System MUST execute 5 independent repetitions for each dataset size and implementation combination (See US-2)
- **FR-006**: System MUST apply Kruskal-Wallis H-test to compare performance differences across the three data structure implementations (See US-3)
- **FR-007**: System MUST generate at least 2 visualization plots: memory vs. set size and latency vs. set size (See US-3)
- **FR-008**: System MUST sample Enron Email Corpus to ≤1,000,000 elements to fit within 14GB disk constraint (See US-2)
- **FR-009**: System MUST use only CPU-tractable methods (no GPU, CUDA, or 8-bit quantization) to ensure compatibility with GitHub Actions free-tier runners (See US-2)

### Key Entities

- **BloomFilter**: Abstract representation of a probabilistic set membership data structure with configurable size, hash count, and underlying storage mechanism
- **BenchmarkRun**: Single execution instance recording memory usage, query latency, and dataset size for one implementation variant
- **Dataset**: Collection of text elements (words or email subjects) used as input for insertion and membership queries

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Memory overhead is measured against theoretical minimum bitset size for each false positive rate target (See US-2)
- **SC-002**: Query latency is measured against native array baseline implementation for each dataset size (See US-2)
- **SC-003**: Statistical significance is measured against α = 0.05 threshold using Kruskal-Wallis H-test p-values (See US-3)
- **SC-004**: Reproducibility is measured against coefficient of variation ≤15% across 5 repetitions per configuration (See US-2)
- **SC-005**: Dataset-variable fit is measured by verifying all required variables (text elements for insertion, membership ground truth) exist in Google 10000 English words and Enron Email Corpus subsets (See US-1)

## Assumptions

- The Google English words dataset URL (https://raw.githubusercontent.com/first20hours/google-10000-english/master/20k.txt) remains accessible throughout the benchmark execution period
- The Enron Email Corpus subset download completes within 30 minutes on GitHub Actions free-tier network bandwidth
- Python 3.10+ or C++17 compiler is available in the GHA runner environment for implementation
- memory_profiler library is installable via pip without CUDA or GPU dependencies
- The Kruskal-Wallis H-test implementation in scipy.stats requires no GPU acceleration and completes within 60 seconds for the expected data volume
- Hash function selection uses MurmurHash3 or similar with deterministic output across runs (no randomness in hash computation)
- Peak memory measurements are taken immediately after insertion phase completes, before query phase begins
- All benchmark scripts execute within the 6-hour GHA job time limit when using the maximum intended dataset size
- The disk constraint is not exceeded by temporary dataset files and benchmark output logs combined
- False positive rate targets ([deferred], [deferred], [deferred]) are achievable within the 7GB RAM constraint for all dataset sizes up to 1,000,000 elements
