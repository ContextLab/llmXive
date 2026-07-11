# Research: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

## Executive Summary

This research extends the "MinT" infrastructure concept by investigating a "Topological Lookahead" scheduling policy for LoRA adapter serving. The core hypothesis is that leveraging the structural similarity (parameter overlap) between adapters can significantly reduce cold-start latency and cache evictions compared to traditional FCFS and frequency-based heuristics. The study relies on a large-scale discrete-event simulation (DES) of a CPU-constrained environment to validate this hypothesis under rigorous statistical testing.

**Key Methodological Innovation**: The study explicitly models the correlation between "parameter overlap" (structural similarity) and "access patterns" (temporal locality) via a tunable coupling coefficient (`alpha`). This ensures the experiment tests the policy's ability to exploit structural signals, rather than validating a straw-man scenario where the trace is random or the policy is circular.

## Dataset Strategy

Since the study involves a novel scheduling policy for a hypothetical infrastructure, no real-world dataset of "LoRA adapter access traces" or "parameter overlap matrices" exists. The research strategy relies on **synthetic data generation** that strictly adheres to the assumptions and constraints defined in the spec.

### 1. Synthetic LoRA Adapters
*   **Source**: Generated programmatically via `code/data_generation/synthetic_adapters.py`.
*   **Method**: Synthesize a substantial set of adapters. Each adapter is defined by a rank $r \in [1, 256]$ and a sparsity pattern (randomly masked weight updates).
*   **Validation**: Ensure generated parameters respect the sparsity constraints and rank bounds.
*   **Constraint**: Must be generated as sparse matrices to fit within 7168 MB RAM.

### 2. Topology Graph Construction
*   **Source**: Computed from the synthetic adapters.
*   **Method**: Calculate pairwise overlap (Jaccard index of non-zero parameter indices) for all adapter pairs.
*   **Representation**: Stored as a sparse adjacency matrix (CSR format) to ensure memory feasibility.
*   **Constraint**: The graph is derived *strictly* from adapter properties, independent of the request trace.

### 3. Correlated Request Trace Generation (Topological Coupling)
*   **Source**: Generated programmatically via `code/data_generation/request_trace.py`.
*   **Method**: Generate a trace of a large volume of requests (or a reduced volume for replications).
*   **Topological Coupling Mechanism**: The trace is generated using a **Markov Chain** where the transition probability $P(A \to B)$ is proportional to the parameter overlap between Adapter A and Adapter B, raised to a power $\alpha$ (the "topology_bias"):
    $$P(A \to B) \propto \text{Overlap}(A, B)^\alpha$$
    *   **$\alpha = 0.0$**: Purely random access (FCFS baseline, Topological policy has no signal).
    *   **$\alpha = 1.0$**: Perfect correlation between overlap and access (ideal scenario for Topological policy).
    *   **Sensitivity Analysis**: The study will vary $\alpha$ from 0.0 to 1.0 to measure the policy's robustness to the strength of the signal.
*   **Hotspots**: The trace also includes "hotspot" clusters to simulate multi-tenant workloads, but the *sequence* within clusters is driven by the Markov Chain.

### Verified Datasets
*No external verified datasets are used.* The study is a computational simulation of a hypothetical scenario. All data is synthetic and generated within the pipeline to ensure full reproducibility and control over variables (rank, sparsity, locality, and topological coupling).

## Literature & Theoretical Context

### MinT Infrastructure
The "MinT: Managed Infrastructure for Training and Serving Millions of LLMs" paper (hypothetical reference for this project's context) proposes a system for managing massive numbers of LoRA adapters. The core challenge identified is the memory bottleneck caused by loading distinct adapter weights into GPU/CPU memory on demand.

**Cost Model Calibration (FR-009)**:
Since no "MinT" hardware benchmarks exist, the simulation cost model is calibrated against **published industry-standard benchmarks** for similar hardware:
*   **I/O Bandwidth**: Based on **PCIe 4.0 x16** throughput (~32 GB/s) as per **Intel Xeon Platinum 8380** datasheet.
*   **Memory Copy**: Based on **DDR4-3200** memory bandwidth (~25 GB/s) as per **Intel Xeon Platinum 8380** memory controller specs.
*   **Latency Calculation**: $Latency = \frac{\text{Adapter Size (MB)}}{\text{Bandwidth (MB/s)}} + \text{Fixed Overhead}$.
This ensures that "latency" metrics are in meaningful milliseconds, not arbitrary units.

### Scheduling Policies
*   **FCFS (First-Come-First-Served)**: The standard baseline. No optimization; simply loads the requested adapter if space permits, otherwise evicts the oldest.
*   **Greedy Frequency**: A heuristic that evicts the least frequently accessed adapter. This is a common approximation for LRU (Least Recently Used) in large-scale systems.
*   **Topological Lookahead**: The proposed innovation. Uses the pre-computed overlap graph to predict which adapters are likely to be needed next based on the current adapter's structural neighbors (high overlap). This exploits the "hotspot" structure of LoRA usage where similar adapters are often requested in sequence.

### Statistical Methodology
To ensure claims of improvement are not artifacts of variance:
*   **Experimental Design**: **Paired Replication Design**.
    1.  **Replication**: Generate a full synthetic dataset (Adapters + Trace) with a unique seed.
    2.  **Paired Execution**: Run this *same* dataset through FCFS, Greedy, and Topological policies.
    3.  **Independence**: Repeat this process for multiple independent replications (regenerating the dataset each time).
    *   *Rationale*: This captures workload variance across replications (inter-replication) while controlling for workload structure within each replication (intra-replication), enabling a valid paired t-test.
*   **Unit of Analysis**: The unit of replication is the *entire synthetic dataset* (100k requests), not individual requests.
*   **Normality Check**: Shapiro-Wilk test on the distribution of latency differences (Topological - FCFS) across the 10 replications.
*   **Significance Test**:
    *   If normal: Paired t-test.
    *   If non-normal: Wilcoxon signed-rank test.
*   **Power**: Achieved via 10 independent replications of the full (Adapter + Trace) generation.
*   **Target**: $p < 0.05$ for the claim of $\ge 15\%$ reduction.
*   **Visualization**: A separate "Full Trace" (1M requests) run is performed once per policy solely for generating final paper figures; it is **not** used for the statistical hypothesis test.

## Feasibility & Constraints Analysis

### Compute Constraints (GitHub Actions Free Tier)
*   **Hardware**: 2 vCPU, ~7 GB RAM, ~14 GB Disk, No GPU.
*   **Time Limit**: 6 hours per job.
*   **Memory**: Hard limit of 7168 MB.

**Feasibility Plan**:
1. **Sparse Matrices**: The [deferred] x [deferred] overlap matrix will be stored as a SciPy `csr_matrix`. With an average sparsity of 90-99%, this will fit comfortably in RAM (estimated < 1 GB).
2.  **SimPy Efficiency**: SimPy is CPU-bound but efficient for event-driven logic. The simulation will be optimized by minimizing Python object creation in the inner loop and using NumPy for vectorized operations where possible.
3. **Trace Sampling**: For the 10 replications required for statistical power, a **100k request sample** will be used. This reduces the event count by a significant factor, ensuring the 6-hour limit is met. A separate "Full Trace" run (1M requests) will be performed once per policy for the final paper figures (visualization only).
4.  **No GPU Dependencies**: All libraries (`numpy`, `scipy`, `simpy`, `pandas`) have pure Python/CPU wheels available. No CUDA or quantization libraries are used.

### Dataset-Variable Fit
*   **Required**: Adapter rank, sparsity pattern, request sequence, memory capacity, topological coupling.
*   **Available**: All generated synthetically with precise control.
*   **Fit**: Perfect. The synthetic generation allows precise control over the "overlap" variable and its correlation with the trace via the `alpha` parameter, which is the independent variable of interest.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use SimPy** | Standard library for DES in Python; supports deterministic event ordering and is lightweight enough for CPU-only CI. |
| **Sparse Matrix for Graph** | Essential to fit the k x 10k overlap matrix in 7GB RAM. Dense matrices would cause OOM during construction. |
| **Synthetic Data Only** | No real-world dataset exists for "LoRA adapter overlap matrices" or "multi-tenant LoRA traces" at this scale. Synthetic data allows controlled experimentation. |
| **10 Independent Replications** | Required to achieve statistical power for the Shapiro-Wilk and t-test/Wilcoxon analysis, ensuring the [deferred] reduction claim is robust against workload variance. |
| **Paired Replication Design** | Regenerating the full dataset per replication captures workload variance, while reusing the same dataset across policies within a replication enables a valid paired test. |
| **Topological Coupling (Alpha)** | Essential to test the hypothesis. The trace must be biased by the topology (via Markov Chain) to provide a signal for the Topological policy. |
| **Cost Model Calibration** | Based on published PCIe/DDR benchmarks (Intel Xeon Platinum 8380) to ensure latency units are physically meaningful, as "MinT" hardware benchmarks are not available. |
| **100k vs 1M Trace Strategy** | 100k requests per replication ensures the 6-hour limit is met while maintaining statistical power. The 1M run is for visualization only. |