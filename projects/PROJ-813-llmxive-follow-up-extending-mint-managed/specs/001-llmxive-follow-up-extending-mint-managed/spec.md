# Feature Specification: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

**Feature Branch**: `001-lora-topology-scheduling`  
**Created**: 2026-08-06  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'MinT: Managed Infrastructure for Training and Serving Millions of LLMs'"

## User Scenarios & Testing

### User Story 1 - Synthetic Data Generation & Topology Construction (Priority: P1)

The system must generate a synthetic dataset of LoRA adapters and compute their pairwise parameter overlap to construct a "LoRA Topology Graph." This is the foundational step; without a valid graph representing structural similarities, no scheduling optimization can occur. The total number of adapters is defined as N = 10,000.

**Why this priority**: This is the data ingestion and preprocessing layer. If the topology graph is not generated correctly or is computationally infeasible on the target hardware, the entire simulation cannot run. It is the prerequisite for all subsequent logic.

**Independent Test**: Can be fully tested by running the data generation script on a CPU-only environment (GitHub Actions ubuntu-latest) and verifying that a valid adjacency matrix (or graph structure) is produced with dimensions matching the specified adapter count (N=10,000), without requiring the simulation engine to be active. The test validates that the matrix is computed via actual linear algebra operations on generated vectors, not hardcoded values.

**Acceptance Scenarios**:

1. **Given** a request to synthesize N = 10,000 adapters with ranks between 1 and 256, **When** the data generation module executes on a GitHub Actions ubuntu-latest (2 vCPU, 7GB RAM) runner, **Then** it outputs a valid parameter overlap matrix where every entry represents the degree of shared weight updates computed via cosine similarity of actual generated weight delta vectors, and the process completes within 45 minutes. The matrix MUST be stored as a sparse structure (CSR) to fit within the available RAM limit.
2. **Given** the generated topology graph, **When** the system validates the graph structure, **Then** it confirms that the graph is symmetric (if overlap is mutual) and contains no NaN or infinite values, ensuring numerical stability for downstream scheduling.

---

### User Story 2 - Discrete-Event Simulation of MinT Infrastructure (Priority: P2)

The system must implement a discrete-event simulation (using SimPy) that models the MinT infrastructure's memory constraints, adapter loading mechanics, and request processing on a CPU-only environment.

**Why this priority**: This is the core execution engine. It allows the system to test scheduling policies against the synthetic workload without needing real GPU hardware. It translates the theoretical topology into measurable system behaviors (latency, evictions).

**Independent Test**: Can be fully tested by running the simulator with a fixed "FCFS" (First-Come-First-Served) baseline policy and a static request trace of a large volume of requests, verifying that the simulation produces a deterministic log of wall-clock time and cache events that matches the theoretical memory constraints.

**Acceptance Scenarios**:

1. **Given** a request trace of 10^6 requests and a fixed memory capacity of sufficient size (simulating the runner's disk-backed swap or a logical memory limit), **When** the simulator runs with the FCFS policy on a GitHub Actions ubuntu-latest (2 vCPU, 7GB RAM) runner, **Then** it records the total wall-clock time and cache eviction count, ensuring the simulation completes within 6 hours and respects the 7GB RAM constraint.
2. **Given** a specific adapter request that exceeds available memory, **When** the simulation executes the eviction logic, **Then** it correctly removes the least recently used or lowest priority adapter and logs the eviction event before loading the new one.

---

### User Story 3 - Greedy Frequency-Based Scheduling Policy (Priority: P2.5)

The system must implement and execute a "Greedy frequency-based" scheduling policy, which evicts adapters based on their historical request frequency to serve as a secondary baseline against the FCFS and Topological Lookahead policies. The Greedy policy uses request frequency from the trace, while the Topological Lookahead policy uses the Proxy Graph; since Cluster IDs are assigned via community detection (noisy) and not perfectly correlated with frequency, the two signals are decoupled, allowing the comparison to isolate the *lookahead* mechanism from simple frequency.

**Why this priority**: This provides a standard heuristic baseline to validate that the Topological Lookahead policy offers improvement over simple frequency-based heuristics, not just FCFS.

**Independent Test**: Can be fully tested by running the simulation with the Greedy policy on the same trace used in US-2, and verifying that the eviction logic prioritizes least-frequently accessed adapters.

**Acceptance Scenarios**:

1. **Given** the request trace and memory constraints, **When** the Greedy policy is executed, **Then** it correctly identifies and evicts the adapters with the lowest historical access frequency when memory is full, verified by comparing the eviction log against a pre-computed ground truth list of lowest-frequency adapters for the given trace.
2. **Given** the results from the Greedy policy run, **When** the statistical analysis module runs, **Then** it records the latency and eviction metrics for comparison against FCFS and Topological Lookahead.

---

### User Story 4 - Topological Lookahead Scheduling Policy Execution (Priority: P3)

The system must implement and execute the "Topological Lookahead" scheduling policy, which utilizes the LoRA Topology Graph to cluster and pre-fetch adapters based on Markov chain request transitions, comparing its performance against the FCFS and Greedy baselines. The research question is refined to: "Does a topology-aware scheduling policy, derived from a fitted graph model, outperform frequency-based heuristics in a simulated environment?" The policy uses a *Proxy Graph* (a noisy approximation of the raw overlap) to avoid tautology.

**Why this priority**: This is the specific innovation being tested. It represents the "solution" to the research question. While P1 and P2 are necessary, this story delivers the specific research value (reduction in cold-start latency via overlap awareness).

**Independent Test**: Can be fully tested by running the simulation with the Topological Lookahead policy on the same trace used in US-2, and statistically comparing the resulting latency distribution against the FCFS and Greedy baselines using a robust statistical test on independent replications.

**Acceptance Scenarios**:

1. **Given** the LoRA Topology Graph, the request trace (generated with topological bias per FR-011), and Markov chain request transitions, **When** the Topological Lookahead policy is executed, **Then** it successfully pre-fetches adapters with high parameter overlap before they are requested, and the system reports the measured percentage reduction in total load operations compared to the FCFS baseline.
2. **Given** the results from the Topological Lookahead, Greedy, and FCFS runs across independent replications (full dataset regeneration per seed), **When** the statistical analysis module runs, **Then** it performs a Shapiro-Wilk normality test on the latency differences, selects a Wilcoxon signed-rank test (or permutation test if distributions are heavy-tailed), and outputs the p-value, test name, and a significance flag (significant if p < 0.05).

### Edge Cases

- **Memory Pressure**: The system MUST detect memory pressure during matrix computation and reduce the adapter count N if the sparse matrix construction exceeds 7GB RAM capacity, logging the reduction and completing the computation within the 6-hour limit.
- **Zero Locality**: The system MUST correctly report that the Topological Lookahead policy yields no improvement over FCFS in a scenario with zero locality (purely random access), rather than crashing or producing NaNs.
- **Timeout**: The system MUST terminate gracefully and report a timeout error with partial results if the simulation exceeds the designated CPU time limit, rather than hanging indefinitely.

## Requirements

### Functional Requirements

- **FR-001**: System MUST synthesize N = 10,000 LoRA adapters with varying ranks (1–256) and random sparsity patterns to generate a representative dataset for simulation (See US-1).
- **FR-002**: System MUST compute a pairwise parameter overlap matrix for all synthesized adapters to construct a LoRA Topology Graph where edge weights represent shared weight updates. The matrix MUST be stored as a sparse structure (CSR) to fit within the 7GB RAM limit (See US-1).
- **FR-003**: System MUST implement a discrete-event simulation environment using SimPy that models memory constraints, adapter loading, and request processing on a CPU-only runner, utilizing a cost model that includes I/O bandwidth, memory copy time, and simulated network contention to ensure non-trivial latency calculation (See US-2).
- **FR-004**: System MUST implement three distinct scheduling policies: FCFS (baseline), Greedy frequency-based, and Topological Lookahead (See US-2, US-3, US-4).
- **FR-005**: System MUST record total wall-clock time, cache hit rates, and eviction counts for each policy run against the same large-scale request trace (See US-4).
- **FR-006**: System MUST perform a statistical significance test (Shapiro-Wilk followed by Wilcoxon signed-rank) comparing the latency distributions of Topological Lookahead against FCFS and Greedy, using multiple independent replications with full dataset regeneration (adapters + trace) per seed to ensure statistical independence. If distributions are heavy-tailed or multimodal, the system MUST use a permutation test with a sufficient number of iterations instead (See US-4).
- **FR-007**: System MUST enforce a hard memory limit and a time limit, terminating gracefully if exceeded (See US-2).
- **FR-008**: System MUST perform a sensitivity analysis on the synthetic sparsity patterns (varying sparsity across levels from low to high) AND the correlation coefficient k (sweeping k over a range of non-negative values) to validate that the Topological Lookahead policy remains robust across different data generation assumptions (See US-1, US-4). Note: Varying k tests the policy's performance under different degrees of workload burstiness; the overlap signal strength is fixed by the Proxy Graph construction.
- **FR-009**: System MUST calibrate the simulation cost model parameters (I/O bandwidth, memory copy time) against standard published CPU I/O bandwidth values (e.g., typical ranges for NVMe and DDR4) before running experiments to ensure the latency metrics reflect real-world physics. (See US-2).
- **FR-010**: System MUST implement a sparse-matrix-first generation strategy with a pruning threshold (overlap < 0.01 ignored) and perform a warm-up verification on a subset of max(a fixed minimum threshold, 0.1 * N) adapters (where N=10,000) to ensure the [deferred]-adapter generation and 10-replication simulation completes within 6 hours, using O(N^2) runtime scaling factor measured on the subset to predict full-scale runtime (See US-1, US-2).
- **FR-011**: System MUST generate the request trace using a latent Cluster ID mechanism where adapters are assigned to clusters based on community detection (Louvain method) on the Proxy Graph, and requests are generated based on cluster affinity (P(Request B | Request A) = base_rate + k * ClusterMatch(A,B)), ensuring a defined topological bias to test the Topological Lookahead policy. The system MUST generate THREE traces: one with k=0.0 (Random Baseline), one with k=0.15 (Moderate Locality), and one with k=0.30 (High Locality). The system MUST ALSO generate an independent validation trace using a different cluster distribution (different seed, k=0.20) with size ^6 requests to ensure the policy generalizes beyond the training generation parameters (essential for generalizability). (See US-4).
- **FR-012**: System MUST correctly report that the Topological Lookahead policy yields no improvement over FCFS in a scenario with zero locality (purely random access), rather than crashing or producing NaNs (See Edge Cases).
- **FR-013**: System MUST terminate gracefully and report a timeout error with partial results if the simulation exceeds the designated CPU time limit, rather than hanging indefinitely (See Edge Cases).
- **FR-014**: System MUST generate the topology graph using a two-stage process: 1) Compute the raw cosine-similarity overlap matrix and threshold it (overlap > 0.01). 2) Fit a Barabási–Albert preferential attachment model to the *degree distribution* of the thresholded graph to generate a "Topological Proxy Graph". The model generates the graph structure (nodes/edges), and overlap values are assigned to edges by sampling from a power-law distribution fitted to the raw cosine-similarity values of the thresholded graph (exponent α=2.1 ± 0.2). This creates a noisy approximation, preventing the policy from simply following a deterministic degree heuristic. The Proxy Graph is used for scheduling, while the raw overlap remains the ground truth (See US-4).
- **FR-015**: System MUST compute all latency and eviction metrics dynamically from actual simulation event timestamps and memory states; the system MUST NOT write hardcoded, placeholder, or simulated metric values to logs or reports. All reported metrics MUST be the result of running the simulation code (See US-4).
- **FR-016**: System MUST initialize project structure with directories: `code/data`, `code/simulation`, `code/analysis`, `tests`, `code/utils`, `data/raw`, `data/processed`, `data/logs`, `docs` (See T001).
- **FR-017**: System MUST generate a `requirements.txt` file containing: `simpy`, `numpy`, `scipy`, `networkx`, `pandas`, `pytest`, `hypothesis` (See T002).
- **FR-018**: System MUST configure linting (ruff) and formatting (black) tools with a `pyproject.toml` configuration file (See T003).
- **FR-019**: System MUST ensure that adapters within the same Cluster ID are generated with high parameter overlap (correlation > 0.8), calculated as the cosine similarity of the flattened, L2-normalized weight delta vectors, ensuring the workload locality signal matches the topology signal (See US-4, FR-011).

### Key Entities

- **LoRA Adapter**: A synthetic entity representing a low-rank adaptation module, characterized by its rank, sparsity pattern, and parameter vector.
- **Topology Graph**: A graph structure where nodes are adapters and weighted edges represent the degree of parameter overlap between them.
- **Request Trace**: A sequence of 10^6 synthetic requests simulating multi-tenant access patterns with defined "hotspots."
- **Simulation Event**: An atomic unit of time in the discrete-event simulation representing an action (load, evict, process request).
- **Cluster ID**: A latent variable assigned to each adapter during generation, used to determine request affinity without exposing the overlap matrix directly to the generation logic.
- **Proxy Graph**: The Barabási-Albert fitted graph used for scheduling, derived from the raw overlap matrix.
- **Contracts**:
  - `contracts/adapter.schema.yaml`: Defines the `LoRA Adapter` entity fields (rank, sparsity, vector).
  - `contracts/request_trace.schema.yaml`: Defines the `Request Trace` entity fields (`is_hotspot`, `cluster_id`).
  - `contracts/simulation_result.schema.yaml`: Defines the `Simulation Result` entity fields (latency, evictions, p-value).
- **Statistical Methods**:
  - `code/analysis/statistics.py`: Implements the Shapiro-Wilk normality test, Wilcoxon signed-rank test, and permutation test for paired differences (fixed topology, regenerated traces).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: System MUST report the percentage reduction in p50 (median) cold-start latency between Topological Lookahead and FCFS, calculated using a cost model based on standard CPU I/O parameters, with a 95% confidence interval computed from actual simulation runs. Success is defined as a reduction ≥ 5% with p < 0.05, or no degradation (reduction > -1% with p > 0.05) if the reduction is < 5% (See US-4).
- **SC-002**: System MUST report the percentage reduction in total cache evictions between Topological Lookahead and FCFS, with a statistically significant confidence interval. Success is defined as a reduction ≥ 5% with p < 0.05, or no degradation (reduction > -1% with p > 0.05) if the reduction is < 5% (See US-4).
- **SC-003**: System MUST report the p-value and test name (Wilcoxon signed-rank or permutation test) for the latency difference, with a significance flag if p < 0.05, using multiple independent replications with full dataset regeneration per seed (See US-4).
- **SC-004**: Simulation execution time is measured against a fixed CPU-only time limit of ≤ 6 hours (wall-clock time) on a GitHub Actions ubuntu-latest (2 vCPU) runner. to ensure compute feasibility (See US-2).
- **SC-005**: Peak RSS memory usage during simulation is measured against a predefined threshold of ≤ 7GB (Peak RSS). to ensure compliance with memory constraints. (See US-2).
- **SC-006**: Average cold-start latency of the Greedy frequency-based policy is measured against the FCFS baseline to establish a secondary performance benchmark (See US-3).
- **SC-007**: System MUST correctly evict the adapter with the lowest historical access frequency when memory is full, verified by comparing the eviction log against a pre-computed ground truth list generated by a deterministic Python script implementing LRU logic on the same trace, stored as a JSON log (See US-3).
- **SC-008**: System MUST report the graph density and overlap distribution of the generated topology graph (See US-1).
- **SC-009**: System MUST verify that the Topological Lookahead policy does not degrade performance (p > 0.05) on the Random Baseline trace (k=0.0), verifying the null hypothesis (See FR-011).
- **SC-010**: System MUST report the clustering coefficient and degree distribution of the generated topology graph to confirm structural consistency across seeds (See FR-014).
- **SC-011**: Verification confirms existence of all required directories: `code/data`, `code/simulation`, `code/analysis`, `tests`, `code/utils`, `data/raw`, `data/processed`, `data/logs`, `docs` (See FR-016).
- **SC-012**: Verification confirms `requirements.txt` exists and contains all listed dependencies (`simpy`, `numpy`, `scipy`, `networkx`, `pandas`, `pytest`, `hypothesis`) (See FR-017).
- **SC-013**: Verification confirms `pyproject.toml` exists and contains valid ruff/black configuration sections (See FR-018).

## Assumptions

- The synthetic data generation (10,000 adapters, 10^6 requests) can be generated and stored as sparse matrices within the available memory constraints of the GitHub Actions free-tier runner, using the pruning threshold (overlap < 0.01) defined in FR-010.
- The parameter overlap calculation can be performed using CPU-tractable linear algebra operations (e.g., sparse matrix multiplication) without requiring GPU acceleration or quantization libraries that depend on CUDA.
- The "MinT" infrastructure's memory constraints and adapter loading mechanics can be accurately approximated by a discrete-event simulation in Python (SimPy) without needing a full C++ or CUDA-based simulation engine.
- The synthetic access trace, generated based on the Cluster ID mechanism defined in FR-011 (k=0.0, 0.15, 0.30, plus validation trace), sufficiently mimics real-world multi-tenant LLM serving patterns to provide valid insights into scheduling efficiency.
- The statistical analysis (Shapiro-Wilk followed by Wilcoxon, or permutation test if needed) is appropriate for the resulting latency distributions when using multiple independent replications with full dataset regeneration per seed.
- A sufficiently large request trace size is sufficient to achieve statistical power for detecting a latency reduction, given the simulation's variance and the full dataset regeneration design.
- The study is framed as a simulation of a hypothetical scenario; the synthetic topology's validity is established through sensitivity analysis of sparsity patterns (FR-008) rather than direct empirical validation against real-world adapter distributions.
- The simulation cost model parameters are calibrated against standard published CPU I/O bandwidth values to ensure the latency metrics are scientifically meaningful. (FR-009).
- All metrics (latency, evictions) are computed dynamically from actual simulation event logs. No hardcoded, placeholder, or fabricated values are allowed in the output.