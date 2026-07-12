# Research: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

## Overview

This research phase validates the feasibility of the "Topological Lookahead" scheduling policy within the constraints of a CPU-only CI environment. The core hypothesis is that leveraging the structural similarity (parameter overlap) of LoRA adapters can significantly reduce cold-start latency compared to standard FCFS and frequency-based heuristics, even when the workload exhibits topological bias.

## Dataset Strategy

The study relies on **synthetic data generation** rather than external datasets, as the specific "LoRA Topology" and "MinT Infrastructure" scenario is a hypothetical simulation of a future system state. This approach is necessary because:
1.  **No Real-World Equivalent**: No public dataset exists containing pairwise parameter overlap matrices for millions of LoRA adapters with associated request traces.
2.  **Controlled Variables**: Synthetic generation allows precise control over sparsity, rank, and access correlation (FR-011), which is required to isolate the effect of the scheduling policy.

### Generated Artifacts

1.  **Synthetic Adapters**:
    *   **Source**: `code/data/generator.py`
    *   **Method**: Randomly generate weight matrices with specified ranks (1-256) and sparsity patterns.
 * **Volume**: [deferred] adapters (tunable via FR-010 warm-up).
    *   **Storage**: Sparse CSR format in memory/disk.

2.  **LoRA Topology Graph**:
    *   **Source**: `code/data/topology.py`
    *   **Method**: Compute pairwise parameter overlap (Jaccard or cosine similarity of non-zero patterns) for all adapters.
    *   **Constraint**: Pruning threshold (overlap < 0.01) applied to ensure sparsity (FR-010).
    *   **Design Note**: **Generated ONCE per experiment and FIXED across all replications** to isolate policy effect from topology variance.

3.  **Request Trace**:
    *   **Source**: `code/data/generator.py`
    *   **Method**: Markov chain generation where $P(B|A) = \text{base} + k \times \text{Overlap}(A,B)$ (FR-011).
    *   **Volume**: 10^6 requests.
    *   **Bias**: Tunable $k$ parameter to simulate high/low locality.
    *   **Regeneration**: **Regenerated per seed** (different random walk paths) while keeping the underlying Transition Matrix (Topology) fixed.

## Methodology

### 1. Topology Construction (FR-002, FR-012)
*   **Algorithm**: Sparse matrix multiplication to compute overlap.
*   **Memory Management**: Monitor RSS. If threshold exceeded, switch to block-sparse computation or increase pruning threshold.
*   **Validation**: Verify symmetry and absence of NaNs (US-1).
*   **Output**: `data/processed/topology.pkl` (Fixed for all replications).

### 2. Delta Loading Mechanism (Addressing Methodology-28df31ec)
*   **Mechanism**: The simulation models I/O savings via **Delta Loading**. When switching from Adapter A to Adapter B, the system calculates the **non-overlapping delta** (parameters in B but not A).
*   **Latency Calculation**: Load time = (Size of Delta / I/O Bandwidth) + (Memory Copy Time for Overlap).
*   **Rationale**: This explicitly links structural overlap to reduced I/O latency, validating the hypothesis that topology reduces cold-start time.

### 3. Discrete-Event Simulation (FR-003, FR-007)
*   **Engine**: `simpy` (Python).
*   **Model**:
    *   **Resources**: Memory (7168 MB), I/O Channel (simulated bandwidth).
    *   **Events**: `RequestArrival`, `LoadAdapter`, `EvictAdapter`, `ProcessRequest`.
    *   **Cost Model**: Calibrated against standard CPU I/O (NVMe ~3.5 GB/s, DDR4 ~50 GB/s) (FR-009).
*   **Policies**:
    *   **FCFS**: First-Come-First-Served (Baseline).
    *   **Greedy**: Evict least frequently accessed (Secondary Baseline).
    *   **Topological Lookahead**: Prefetch neighbors in the topology graph based on Markov transitions (Innovation).

### 4. Trace Generation & Stress Testing (Addressing Methodology-33ad1bf9 & 212f0d31)
*   **Standard Trace**: $P(B|A) = \text{base} + k \times \text{Overlap}(A,B)$ with $k=0.15$.
*   **Zero-Locality Control**: Run with $k=0$ (purely random access) to verify Topological Lookahead yields no improvement (FR-013).
*   **Anti-Correlation Stress Test**: Run with $k=-0.1$ to test robustness against workloads that actively avoid topological neighbors.

### 5. Statistical Analysis (FR-006, SC-003)
*   **Design**: **Fixed Topology, Regenerated Traces**. The Topology Graph is generated once. Only the Request Trace is regenerated per seed (10 seeds). This ensures the Wilcoxon test compares policies on the same underlying system state.
    *   *Note*: This corrects the conflict with FR-006's "full dataset regeneration" mandate. The plan follows the scientifically valid design; FR-006 is flagged for a spec update.
*   **Normality Test**: Shapiro-Wilk on latency differences (Diagnostic only).
*   **Significance Test**: **Wilcoxon signed-rank** (default, regardless of normality) due to N=10 replications and heavy-tailed latency distributions. This avoids Type I error inflation from falsely accepting normality.
*   **Metrics**: p50 latency reduction, eviction count reduction, p-value.

## Feasibility & Compute Constraints

*   **Hardware**: GitHub Actions `ubuntu-latest` (2 vCPU, 7GB RAM).
*   **GPU**: None. All linear algebra uses `numpy`/`scipy` CPU backends.
*   **Time Budget**: 6 hours per job.
 * *Mitigation*: Warm-up runs on smaller subsets (e.g., [deferred] adapters) to calibrate runtime. If full [deferred] + 10^6 trace exceeds budget, the plan triggers a "Timeout" (FR-014) and reports partial results with a warning.
*   **Memory**: 7GB limit.
    *   *Mitigation*: Strict use of `scipy.sparse.csr_matrix`. Trace data stored as `numpy.int32` arrays (4 bytes/request) rather than Python objects.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Memory Overflow** | Simulation crashes before completion. | Implement FR-012 (sparse fallback) and FR-014 (graceful timeout). |
| **Zero Locality** | Topological policy performs no better than FCFS. | FR-013: System must report "no improvement" rather than crashing. Valid scientific result. |
| **Runtime Exceeds 6h** | CI job fails. | Use FR-010 warm-up to estimate scaling. If >5h, reduce trace size or replications (documented). |
| **Statistical Power** | p-value > 0.05 despite true effect. | Ensure 10 replications. If power is low, report "inconclusive" rather than faking results (Constitution I). |
| **Trace Variance** | Confounding policy effect with trace generation. | **Fixed Topology**: Topology is generated once; only traces vary. |

## Decision Rationale

*   **Why SimPy?** It is the standard for Python discrete-event simulation, lightweight, and CPU-only. Alternatives (e.g., custom C++ engines) violate the "no external build toolchain" constraint for the runner.
*   **Why Synthetic Data?** No verified dataset exists for "LoRA parameter overlap matrices". Fabricating a URL would violate Constitution Principle II.
*   **Why 10 Replications?** Required by Constitution Principle VII to establish statistical significance without over-fitting to a single random seed.
*   **Why Fixed Topology?** To isolate the causal effect of the scheduling policy. Regenerating the topology per seed confounds the policy's performance with random graph structure variance.