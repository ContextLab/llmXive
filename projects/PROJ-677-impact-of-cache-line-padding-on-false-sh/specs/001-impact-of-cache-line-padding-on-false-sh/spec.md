# Feature Specification: Impact of Cache Line Padding on False Sharing in Concurrent Counters

**Feature Branch**: `001-cache-line-padding-false-sharing`  
**Created**: 2026-06-08  
**Status**: Draft  
**Input**: User description: "How does cache-line padding of thread-local counters affect memory bus contention and throughput under high-frequency concurrent updates on multi-core processors?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Benchmark Harness Setup and Compilation (Priority: P1)

Set up the C++ benchmark harness and compile both counter variants (packed and padded) with optimization flags on the GitHub Actions runner.

**Why this priority**: Without a working compiled benchmark, no experiments can be executed. This is the foundational dependency for all downstream measurement and analysis.

**Independent Test**: Can be fully tested by compiling the C++ code with `g++ -O3 -march=native` and verifying the executable runs without errors on a single-threaded test run.

**Acceptance Scenarios**:

1. **Given** the C++ source files are in the repository, **When** the build script executes with `-O3 -march=native` flags, **Then** the compiled binary produces zero warnings and exits with code 0
2. **Given** the compiled binary exists, **When** run with thread count = 1, **Then** the benchmark completes within 300 seconds and outputs timing data to stdout

---

### User Story 2 - Multi-Threaded Experiment Execution (Priority: P2)

Execute the benchmark across all thread counts (1, 2, 4, 8) and both counter configurations (packed, padded), performing a large number of atomic increments per thread and recording wall-clock time over multiple repetitions.

**Why this priority**: This generates the core empirical data needed to quantify the padding effect. Without this data, no statistical analysis is possible.

**Independent Test**: Can be fully tested by running the benchmark binary with explicit thread-count and configuration parameters, verifying CSV output is generated with ≥5 timing samples per configuration.

**Acceptance Scenarios**:

1. **Given** the benchmark binary is compiled, **When** executed with thread count = 8 and configuration = padded, **Then** the job completes within 6 hours and produces ≥5 timing measurements in CSV format
2. **Given** a completed experiment run, **When** the CSV is parsed, **Then** each row contains thread_count, configuration, iteration_count, and wall_clock_time_ms with no missing values

---

### User Story 3 - Statistical Analysis and Visualization (Priority: P3)

Perform two-sample t-tests comparing padded vs. unpadded throughput at each thread count, compute effect sizes (Cohen's d), and generate a line plot with 95% confidence intervals.

**Why this priority**: This transforms raw timing data into interpretable findings that answer the research question. It is the final deliverable but depends on US-2 data.

**Independent Test**: Can be fully tested by running the analysis script on sample CSV data and verifying the output includes p-values, effect sizes, and a generated plot file.

**Acceptance Scenarios**:

1. **Given** a CSV with ≥5 timing samples per configuration, **When** the analysis script executes, **Then** it outputs t-test results (t-statistic, p-value) for each thread count comparison
2. **Given** the analysis completes successfully, **When** the output directory is inspected, **Then** a PNG plot file exists showing thread count (x-axis) vs. throughput (y-axis) with 95% CI error bars

---

### Edge Cases

- What happens when the GitHub Actions runner has fewer than 8 physical cores? (System MUST gracefully execute with available core count and log a warning)
- How does system handle compilation failure on the runner? (Build MUST fail fast with exit code 1 and output compiler error messages to GitHub Actions logs)
- What happens when timing measurements exceed 6 hours total? (Job MUST be terminated by GitHub Actions timeout; analysis MUST flag incomplete data)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compile C++ benchmark harness with `-O3 -march=native` flags using `g++` on the GitHub Actions runner (See US-1)
- **FR-002**: System MUST implement two counter variants: (a) packed `struct { long c1; long c2; long c3; }` with `#pragma pack(1)` to ensure 24-byte total size, and (b) padded `struct { alignas(64) long c1; alignas(64) long c2; alignas(64) long c3; }` where the struct size is ≥ 192 bytes to guarantee each member resides in a separate 64-byte cache line (See US-1)
- **FR-003**: System MUST support worker thread counts N ∈ {1, 2, 4, 8} via command-line parameter (See US-2)
- **FR-004**: System MUST perform exactly 10⁷ atomic increments per thread using `std::atomic<long>` (See US-2)
- **FR-005**: System MUST record wall-clock time for each thread-count/configuration pair across at least 5 independent runs and compute mean operations-per-second (See US-2)
- **FR-006**: System MUST output raw timing data in CSV format with columns: thread_count, configuration, iteration_count, wall_clock_time_ms (See US-2)
- **FR-007**: System MUST apply two-sample t-test (α = 0.05) comparing padded vs. unpadded throughput at each thread count (See US-3)
- **FR-008**: System MUST compute and report effect size (Cohen's d) for each thread-count comparison (See US-3)
- **FR-009**: System MUST generate a line plot (thread count vs. throughput) with 95% confidence intervals calculated using the t-distribution with n-1 degrees of freedom, using Python matplotlib (See US-3)
- **FR-010**: System MUST allocate counters in a shared array where each thread writes to a distinct element, ensuring the 'packed' variant induces false sharing within a single cache line (See US-2)

### Key Entities

- **BenchmarkRun**: A single execution of the C++ binary with specific thread count and configuration; attributes include thread_count, configuration, iteration_count, wall_clock_time_ms
- **AggregatedResult**: Mean throughput and standard deviation across at least 5 runs for a given thread_count/configuration pair
- **StatisticalComparison**: T-test results (t-statistic, p-value, Cohen's d) comparing padded vs. unpadded at a specific thread count

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Throughput (operations-per-second) is measured against thread count and counter configuration (See US-2)
- **SC-002**: Statistical significance (p-value) is measured against α = 0.05 threshold for each thread-count comparison (See US-3)
- **SC-003**: Effect size (Cohen's d) is measured against conventional benchmarks (small ≥ 0.2, medium ≥ 0.5, large ≥ 0.8) for each comparison (See US-3)
- **SC-004**: Measurement validity is ensured by using atomic operations (`std::atomic<long>`) to prevent compiler optimization from eliminating increments (See US-2)
- **SC-005**: Multiplicity control is applied via the Benjamini-Hochberg False Discovery Rate (FDR) procedure at q ≤ 0.05 across the 4 thread counts, consistent with standard practice in performance benchmarking where multiple correlated comparisons are made (see Benjamini & Hochberg, 1995). If the FDR-adjusted p-value for any thread count is ≤ 0.05, the difference is declared significant. (See US-3)

## Assumptions

- **Assumption 1**: The GitHub Actions runner has ≥2 CPU cores and ~7 GB RAM, sufficient for compiling and running the C++ benchmark without GPU acceleration
- **Assumption 2**: Cache line size is a fixed architectural parameter on the target architecture; the `alignas(64)` directive will achieve proper padding
- **Assumption 3**: The workload (10⁷ increments per thread) is sufficiently large to measure throughput differences but small enough to complete within 6 hours total
- **Assumption 4**: The atomic instruction overhead is a constant across both variants; the variable of interest is the latency penalty of cache-line bouncing (false sharing), not the atomic instruction cost itself
- **Assumption 5**: The analysis is observational (no random assignment of threads to cores); findings will be framed as ASSOCIATIONAL between padding and throughput, not causal
- **Assumption 6**: Power/sample-size considerations are deferred; the fixed design (5 runs × 4 thread counts × 2 configurations) is assumed adequate for detecting medium-to-large effects (Cohen's d ≥ 0.5)