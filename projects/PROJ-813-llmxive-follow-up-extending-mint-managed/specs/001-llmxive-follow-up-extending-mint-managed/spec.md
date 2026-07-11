# Feature Specification: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

**Feature Branch**: `001-lrmxive-lora-topology-scheduling`  
**Created**: 2026-07-05  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending MinT infrastructure to optimize multi-tenant LLM serving via parameter overlap clustering of LoRA adapters"

## User Scenarios & Testing

### User Story 1 - Synthetic Workload Generation & Topology Construction (Priority: P1)

The research engineer must be able to generate a synthetic dataset of LoRA adapters with varying ranks and sparsity patterns, explicitly injecting correlation between base weights to ensure non-trivial overlap variance, and compute a pairwise parameter overlap matrix to construct a "LoRA Topology Graph" where edge weights represent the degree of shared weight updates.

**Why this priority**: This is the foundational data layer. Without a valid topology graph derived from the adapters, no overlap-aware scheduling can occur. This step establishes the "predictor" variable (structural similarity) required for the entire study.

**Independent Test**: Can be fully tested by running the data generation script and verifying the existence of the adjacency matrix file and its dimensionality ([deferred] x [deferred]) without executing any simulation logic.

**Acceptance Scenarios**:

1. **Given** a configuration for [deferred] adapters with ranks in [1, 256], **When** the generation script executes, **Then** a JSON or CSV file containing the pairwise overlap matrix is created with values between 0.0 and 1.0, calculated as `(cosine_similarity + 1) / 2` to ensure the normalized range.
2. **Given** the generated overlap matrix, **When** a graph construction utility runs, **Then** an undirected graph object is returned where nodes represent adapters and edge weights match the overlap values within a tolerance of 1e-6.

---

### User Story 2 - Discrete-Event Simulation of MinT Infrastructure (Priority: P1)

The system must implement a discrete-event simulation (using SimPy) that models the MinT infrastructure's memory constraints, adapter loading mechanics (including a stochastic jitter component of ±10% to simulate real-world variance), and cache eviction policies on a CPU-only environment, capable of processing a trace of a substantial volume of requests.

**Why this priority**: This provides the "environment" for the experiment. It must accurately model the hardware constraints (memory, CPU) and include stochastic elements to ensure the results reflect real-world feasibility rather than theoretical ideals or mathematical identities.

**Independent Test**: Can be fully tested by running the simulation with a "No-Op" policy (instant load) and a "FCFS" policy against a small trace ([deferred] requests) to verify that memory usage never exceeds the configured limit and that request processing order matches the input trace.

**Acceptance Scenarios**:

1. **Given** a memory limit of 7 GB and a trace of [deferred] requests, **When** the simulation runs with the FCFS policy, **Then** the total wall-clock time is recorded, and no memory overflow errors occur (defined as the simulation raising a `MemoryLimitExceeded` event or assertion failure if current_memory > 7 GB).
2. **Given** a specific request trace, **When** the simulation processes a request for an adapter not in cache, **Then** the system records a "cache miss" event and triggers a load operation that consumes simulated time proportional to the adapter size plus a random jitter of ±10%.

---

### User Story 3 - Policy Comparison & Statistical Validation (Priority: P2)

The system must execute the simulation under three distinct policies (FCFS, Greedy Frequency, Topological Lookahead using Markov chain request transitions) against the same trace, running multiple independent replications with different random seeds., and apply a block-bootstrapping approach (or paired t-test on replication means) to compare the latency distributions of the Topological Lookahead policy against the FCFS baseline.

**Why this priority**: This delivers the core research output: the comparative analysis. It transforms raw simulation data into a statistically significant conclusion regarding the efficacy of the proposed optimization, ensuring validity against autocorrelation.

**Independent Test**: Can be fully tested by running the analysis script on a pre-generated set of simulation logs to verify that the statistical test returns a p-value and that the mean latency difference is calculated correctly across replications.

**Acceptance Scenarios**:

1. **Given** simulation logs from 30 independent replications of FCFS and Topological Lookahead policies, **When** the analysis script runs, **Then** a block-bootstrapping analysis (or paired t-test on replication means) is performed, and a p-value < 0.05 is reported if the improvement is significant.
2. **Given** the comparison results, **When** the report is generated, **Then** it explicitly states whether the Topological Lookahead policy reduced average cold-start latency by at least 15% compared to the FCFS baseline, outputting a boolean `PASS` or `FAIL` based on this threshold.

---

### Edge Cases

- What happens if the synthetic trace contains a "cold start" request for an adapter that was never loaded and the memory is full? (System must evict the least recently used or least relevant adapter based on the policy).
- How does the system handle a scenario where the parameter overlap calculation results in a fully disconnected graph (no shared parameters)? (The Topological Lookahead policy must degrade gracefully to a frequency-based or random strategy without crashing).
- What occurs if the simulated memory limit is exceeded during a bulk load operation? (The simulation must log an error event and either fail the request or trigger an immediate eviction sequence, depending on the policy configuration).

## Requirements

### Functional Requirements

- **FR-001**: The system MUST generate a large corpus of synthetic LoRA adapters with ranks uniformly distributed between 1 and 256, random sparsity patterns, and explicitly injected correlations in base weights to ensure non-trivial overlap variance, serving as the dataset for the study (See US-1).
- **FR-002**: The system MUST compute a pairwise parameter overlap matrix for all generated adapters and construct an undirected graph where edge weights represent the degree of shared weight updates (See US-1).
- **FR-003**: The system MUST implement a discrete-event simulation engine using SimPy that enforces a strict memory cap, models adapter loading latency proportional to adapter size, and includes a stochastic jitter component of ±10% to prevent tautological validation (See US-2).
- **FR-004**: The system MUST support three distinct scheduling policies: (1) First-Come-First-Served (FCFS), (2) Greedy frequency-based loading, and (3) Topological Lookahead using Markov chain request transitions (See US-2, US-3).
- **FR-005**: The system MUST execute the simulation for a trace of requests across 30 independent replications and record total wall-clock time, cache hit rates, and eviction counts for each policy (See US-3).
- **FR-006**: The system MUST perform a statistical comparison (block-bootstrapping or paired t-test on replication means) between the latency distributions of the Topological Lookahead and FCFS policies to determine significance (See US-3).

### Non-Functional Requirements

- **NFR-001**: The simulation must complete within 6 hours on a standard GitHub Actions free-tier runner to ensure feasibility (See US-2).

### Key Entities

- **LoRA Adapter**: A synthetic model component defined by its rank, sparsity pattern, base weight correlation, and parameter weight matrix.
- **Topology Graph**: An undirected graph structure where nodes are adapters and edge weights are the calculated parameter overlap values.
- **Access Trace**: A time-ordered sequence of [deferred] requests, each targeting a specific adapter ID.
- **Simulation Event**: A discrete point in time representing a request arrival, adapter load, cache eviction, or request completion.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Average cold-start latency is measured against the FCFS baseline to determine the percentage reduction (See US-3).
- **SC-002**: Cache eviction count is measured against the FCFS baseline to verify if the Topological Lookahead policy reduces unnecessary evictions (See US-3).
- **SC-003**: Statistical significance of the latency improvement is measured against a p-value threshold of 0.05 using block-bootstrapping or a paired t-test on replication means (See US-3).
- **SC-004**: Memory usage during simulation is measured against the 7 GB RAM limit to ensure the workload fits within the free-tier runner constraints (See US-2).

## Assumptions

- The synthetic dataset generation (a large number of adapters, a substantial volume of requests) will fit within the memory and disk limits of the GitHub Actions free-tier runner when processed in batches or via efficient data structures.
- The "Topological Lookahead" policy will utilize a simplified Markov chain approximation for request transitions to ensure the scheduling decision overhead remains negligible compared to the simulated load time, preventing the scheduler itself from becoming a bottleneck.
- The parameter overlap metric is defined as the cosine similarity of the flattened weight vectors of the LoRA adapters, normalized to [0.0, 1.0] via `(cosine_sim + 1) / 2`, which is computationally tractable on CPU for the specified dataset size.
- The simulation time unit is abstract and relative; absolute wall-clock time in the simulation is a proxy for real-world latency, scaled by a constant factor derived from typical PCIe/NVMe transfer speeds.
- The statistical power of the test is sufficient with N=30 independent replications; if the effect size is very small, the analysis will report a confidence interval rather than a binary significance claim.
- No GPU acceleration is required or available; all computations (overlap matrix, simulation logic, statistical tests) are performed using standard CPU libraries (NumPy, SciPy, SimPy).
- The simulation must complete within 6 hours on a standard GitHub Actions free-tier runner; if it exceeds this, the trace size or replication count will be reduced.