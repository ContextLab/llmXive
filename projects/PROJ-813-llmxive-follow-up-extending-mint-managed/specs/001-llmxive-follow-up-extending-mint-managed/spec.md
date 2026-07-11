# Feature Specification: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

**Feature Branch**: `001-lora-topology-scheduling`  
**Created**: 2026-07-05  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'MinT: Managed Infrastructure for Training and Serving Millions of LLMs'"

## User Scenarios & Testing

### User Story 1 - Synthetic Data Generation & Topology Construction (Priority: P1)

The system must generate a synthetic dataset of 10,000 LoRA adapters and compute their pairwise parameter overlap to construct a "LoRA Topology Graph." This is the foundational step; without a valid graph representing structural similarities, no scheduling optimization can occur.

**Why this priority**: This is the data ingestion and preprocessing layer. If the topology graph is not generated correctly or is computationally infeasible on the target hardware, the entire simulation cannot run. It is the prerequisite for all subsequent logic.

**Independent Test**: Can be fully tested by running the data generation script on a CPU-only environment (GitHub Actions ubuntu-latest, 2 vCPU, 7GB RAM) and verifying that a valid adjacency matrix (or graph structure) is produced with dimensions matching [deferred] synthesized adapters, without requiring the simulation engine to be active.

**Acceptance Scenarios**:

1. **Given** a request to synthesize [deferred] adapters with ranks between 1 and 256, **When** the data generation module executes on a GitHub Actions ubuntu-latest (2 vCPU, 7GB RAM) runner, **Then** it outputs a valid parameter overlap matrix where every entry represents the degree of shared weight updates, and the process completes within a wall-clock time budget of 6 hours.
2. **Given** the generated topology graph, **When** the system validates the graph structure, **Then** it confirms that the graph is symmetric (if overlap is mutual) and contains no NaN or infinite values, ensuring numerical stability for downstream scheduling.

---

### User Story 2 - Discrete-Event Simulation of MinT Infrastructure (Priority: P2)

The system must implement a discrete-event simulation (using SimPy) that models the MinT infrastructure's memory constraints, adapter loading mechanics, and request processing on a CPU-only environment.

**Why this priority**: This is the core execution engine. It allows the system to test scheduling policies against the synthetic workload without needing real GPU hardware. It translates the theoretical topology into measurable system behaviors (latency, evictions).

**Independent Test**: Can be fully tested by running the simulator with a fixed "FCFS" (First-Come-First-Served) baseline policy and a static request trace of 10^6 requests, verifying that the simulation produces a deterministic log of wall-clock time and cache events that matches the theoretical memory constraints.

**Acceptance Scenarios**:

1. **Given** a request trace of 10^6 requests and a fixed memory capacity of 7168 MB, **When** the simulator runs with the FCFS policy, **Then** it records the total wall-clock time and cache eviction count, ensuring the simulation completes within 6 hours and respects the 7168 MB RAM constraint.
2. **Given** a specific adapter request that exceeds available memory, **When** the simulation executes the eviction logic, **Then** it correctly removes the least recently used or lowest priority adapter and logs the eviction event before loading the new one.

---

### User Story 3 - Greedy Frequency-Based Scheduling Policy (Priority: P2.5)

The system must implement and execute a "Greedy frequency-based" scheduling policy, which evicts adapters based on their historical request frequency to serve as a secondary baseline against the FCFS and Topological Lookahead policies.

**Why this priority**: This provides a standard heuristic baseline to validate that the Topological Lookahead policy offers improvement over simple frequency-based heuristics, not just FCFS.

**Independent Test**: Can be fully tested by running the simulation with the Greedy policy on the same trace used in US-2, and verifying that the eviction logic prioritizes least-frequently accessed adapters.

**Acceptance Scenarios**:

1. **Given** the request trace and memory constraints, **When** the Greedy policy is executed, **Then** it correctly identifies and evicts the adapters with the lowest historical access frequency when memory is full.
2. **Given** the results from the Greedy policy run, **When** the statistical analysis module runs, **Then** it records the latency and eviction metrics for comparison against FCFS and Topological Lookahead.

---

### User Story 4 - Topological Lookahead Scheduling Policy Execution (Priority: P3)

The system must implement and execute the "Topological Lookahead" scheduling policy, which utilizes the LoRA Topology Graph to cluster and pre-fetch adapters based on Markov chain request transitions, comparing its performance against the FCFS and Greedy baselines.

**Why this priority**: This is the specific innovation being tested. It represents the "solution" to the research question. While P1 and P2 are necessary, this story delivers the specific research value (reduction in cold-start latency via overlap awareness).

**Independent Test**: Can be fully tested by running the simulation with the Topological Lookahead policy on the same trace used in US-2, and statistically comparing the resulting latency distribution against the FCFS and Greedy baselines using a robust statistical test on independent replications.

**Acceptance Scenarios**:

1. **Given** the LoRA Topology Graph, the request trace, and Markov chain request transitions, **When** the Topological Lookahead policy is executed, **Then** it successfully pre-fetches adapters with high parameter overlap before they are requested, achieving a ≥ 15% reduction in the total number of load operations compared to the FCFS baseline with statistical significance (p < 0.05).
2. **Given** the results from the Topological Lookahead, Greedy, and FCFS runs across 10 independent replications, **When** the statistical analysis module runs, **Then** it performs a Shapiro-Wilk normality test on the latency differences and selects a paired t-test or Wilcoxon signed-rank test (with block bootstrapping) to determine if the latency reduction is statistically significant (p < 0.05).

### Edge Cases

- What happens when the parameter overlap matrix is too large to fit in RAM (e.g., >10,000 adapters)? The system MUST fall back to a sparse matrix representation or a sampled subset to remain within the available RAM limit.
- How does the system handle a request trace with zero locality (purely random access)? The system MUST correctly report that the Topological Lookahead policy yields no improvement over FCFS in this scenario, rather than crashing or producing NaNs.
- What happens if the simulation exceeds the designated CPU time limit? The system MUST terminate gracefully and report a timeout error with partial results if available, rather than hanging indefinitely.

## Requirements

### Functional Requirements

- **FR-001**: System MUST synthesize [deferred] LoRA adapters with varying ranks (1–256) and random sparsity patterns to generate a representative dataset for simulation (See US-1).
- **FR-002**: System MUST compute a pairwise parameter overlap matrix for all synthesized adapters to construct a LoRA Topology Graph where edge weights represent shared weight updates (See US-1).
- **FR-003**: System MUST implement a discrete-event simulation environment using SimPy that models memory constraints, adapter loading, and request processing on a CPU-only runner, utilizing a cost model that includes I/O bandwidth, memory copy time, and simulated network contention to ensure non-trivial latency calculation (See US-2).
- **FR-004**: System MUST implement three distinct scheduling policies: FCFS (baseline), Greedy frequency-based, and Topological Lookahead (See US-2, US-3, US-4).
- **FR-005**: System MUST record total wall-clock time, cache hit rates, and eviction counts for each policy run against the same large-scale request trace (See US-4).
- **FR-006**: System MUST perform a statistical significance test (Shapiro-Wilk followed by paired t-test or Wilcoxon signed-rank) comparing the latency distributions of Topological Lookahead against FCFS and Greedy, using block bootstrapping or 10 independent replications to ensure statistical independence (See US-4).
- **FR-007**: System MUST enforce a hard memory limit of 7168 MB and a time limit of 6 hours, terminating gracefully if exceeded (See US-2).
- **FR-008**: System MUST perform a sensitivity analysis on the synthetic sparsity patterns (e.g., varying sparsity from [deferred] to [deferred]) to validate that the Topological Lookahead policy remains robust across different data generation assumptions (See US-1, US-4).
- **FR-009**: System MUST calibrate the simulation cost model parameters (I/O bandwidth, memory copy time) against published MinT hardware benchmarks before running experiments to ensure the latency metrics reflect real-world performance (See US-2).

### Key Entities

- **LoRA Adapter**: A synthetic entity representing a low-rank adaptation module, characterized by its rank, sparsity pattern, and parameter vector.
- **Topology Graph**: A graph structure where nodes are adapters and weighted edges represent the degree of parameter overlap between them.
- **Request Trace**: A sequence of 10^6 synthetic requests simulating multi-tenant access patterns with defined "hotspots."
- **Simulation Event**: An atomic unit of time in the discrete-event simulation representing an action (load, evict, process request).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: p50 (median) cold-start latency in milliseconds is measured against the First-Come-First-Served (FCFS) baseline to determine the percentage reduction, calculated using a cost model including I/O bandwidth, memory copy time, and simulated network contention, with a target reduction of ≥ 15% (See US-4).
- **SC-002**: Total number of cache evictions is measured against the FCFS baseline to quantify resource efficiency gains, with a target reduction of ≥ 15% (See US-4).
- **SC-003**: Statistical significance of the latency difference is measured against a p-value threshold of 0.05 using a paired t-test or Wilcoxon signed-rank test, selected based on the result of a Shapiro-Wilk normality test on the difference distribution, utilizing block bootstrapping or 10 independent replications (See US-4).
- **SC-004**: Simulation execution time is measured against a predefined CPU-only time limit of 6 hours on a GitHub Actions ubuntu-latest (2 vCPU) runner, to ensure compute feasibility (See US-2).
- **SC-005**: Peak RSS memory usage during simulation is measured against a hard limit of 7168 MB to ensure compliance with system resource constraints (See US-2).
- **SC-006**: Average cold-start latency of the Greedy frequency-based policy is measured against the FCFS baseline to establish a secondary performance benchmark (See US-3).

## Assumptions

- The synthetic data generation (a large number of adapters, a high volume of requests) can be generated and stored as sparse matrices within the available memory constraints of the GitHub Actions free-tier runner.
- The parameter overlap calculation can be performed using CPU-tractable linear algebra operations (e.g., matrix multiplication) without requiring GPU acceleration or quantization libraries that depend on CUDA.
- The "MinT" infrastructure's memory constraints and adapter loading mechanics can be accurately approximated by a discrete-event simulation in Python (SimPy) without needing a full C++ or CUDA-based simulation engine.
- The synthetic access trace, generated based on "hotspots," sufficiently mimics real-world multi-tenant LLM serving patterns to provide valid insights into scheduling efficiency.
- The statistical analysis (Shapiro-Wilk followed by t-test or Wilcoxon) is appropriate for the resulting latency distributions when using block bootstrapping or independent replications.
- A sufficiently large request trace size is sufficient to achieve statistical power for detecting a latency reduction, given the simulation's variance.
- The study is framed as a simulation of a hypothetical scenario; the synthetic topology's validity is established through sensitivity analysis of sparsity patterns (FR-008) rather than direct empirical validation against real-world adapter distributions.
- The simulation cost model parameters are calibrated against published MinT hardware benchmarks to ensure the latency metrics are scientifically meaningful (FR-009).