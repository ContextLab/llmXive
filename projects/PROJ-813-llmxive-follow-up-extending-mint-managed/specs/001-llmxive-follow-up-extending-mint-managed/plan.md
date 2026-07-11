# Implementation Plan: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

**Branch**: `001-lora-topology-scheduling` | **Date**: 2026-07-05 | **Spec**: `spec.md`
**Input**: Feature specification for LoRA Topology Scheduling simulation.

## Summary

This project implements a discrete-event simulation (DES) to evaluate a "Topological Lookahead" scheduling policy for serving millions of LoRA adapters, extending the "MinT" infrastructure concept. The system synthesizes [deferred] LoRA adapters with varying ranks and sparsity, constructs a pairwise parameter overlap graph, and simulates request traces on a CPU-constrained environment (7168 MB RAM, 6h limit). It compares three policies: FCFS, Greedy Frequency-based, and the proposed Topological Lookahead, measuring cold-start latency and eviction counts with rigorous statistical testing.

**Key Methodological Correction**: To ensure scientific validity, the request trace is generated with a tunable "topological coupling" parameter (`alpha`) that correlates access patterns with parameter overlap via a Markov Chain. The experiment runs 10 independent replications, where **each replication regenerates the full (Adapters + Trace) dataset with a unique seed**. This ensures workload variance is captured in the statistical test, while the paired design (same dataset for all policies within a replication) controls for workload structure. The statistical conclusion is drawn from multiple replications of request samples; a separate large-scale request run is performed once per policy solely for visualization.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `simpy` (discrete-event simulation), `numpy` (linear algebra/sparse matrices), `scipy` (statistical tests), `networkx` (graph construction), `pandas` (data handling), `pytest` (testing).  
**Storage**: In-memory data structures (NumPy sparse arrays, Pandas DataFrames); artifacts written to `data/` as CSV/Parquet/JSON.  
**Testing**: `pytest` with strict random seed pinning for reproducibility.  
**Target Platform**: GitHub Actions `ubuntu-latest` (2 vCPU, ~7 GB RAM, CPU-only).  
**Project Type**: Computational Research Simulation / CLI.  
**Performance Goals**: Complete 10^6 request trace simulation with statistical replications within 6 hours wall-clock time; peak RSS < 7168 MB.  
**Constraints**: No GPU/CUDA; must handle sparse matrix representations for the overlap graph; must enforce hard memory/time limits; statistical significance (p < 0.05) required for claims.  
**Scale/Scope**: A large set of synthetic adapters; 10^6 synthetic requests (or sampled 100k for rapid replications); 10 independent replications per policy.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. `requirements.txt` pins versions. SimPy environment configured for deterministic event ordering. |
| **II. Verified Accuracy** | **PASS** | All citations (MinT benchmarks, statistical methods) will be validated against primary sources (e.g., **Intel Xeon Platinum 8380** datasheet for cost model) before inclusion in `research.md`. |
| **III. Data Hygiene** | **PASS** | Synthetic data generation scripts will output checksums. No in-place modifications; derivations stored as new files in `data/`. |
| **IV. Single Source of Truth** | **PASS** | Figures and statistics in the final paper will be generated programmatically from `data/` artifacts using `code/analysis/statistics.py` (specifically implementing **Shapiro-Wilk** and **paired t-tests**). |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes; `state/` YAML updated on changes. |
| **VI. Simulation Determinism & Topological Fidelity** | **PASS** | SimPy `random` seed fixed per replication. Topology graph derived *strictly* from adapter properties (rank/sparsity), independent of request trace generation logic (which uses a separate coupling parameter `alpha`). |
| **VII. Statistical Rigor in Latency Evaluation** | **PASS** | Plan mandates **Shapiro-Wilk test** (in `code/analysis/statistics.py`) followed by **paired t-test** or **Wilcoxon signed-rank test**. 10 independent replications (full dataset regeneration) used for independence. |

## Project Structure

### Documentation (this feature)

```text
specs/001-lora-topology-scheduling/
├── plan.md              # This file
├── research.md          # Phase 0 output (Dataset strategy, literature review)
├── data-model.md        # Phase 1 output (Schema definitions)
├── quickstart.md        # Phase 1 output (Setup and run instructions)
├── contracts/           # Phase 1 output (YAML schemas for validation)
│   ├── adapter.schema.yaml
│   ├── request_trace.schema.yaml
│   ├── simulation-result.schema.yaml
│   └── topology-graph-schema.schema.yaml
└── tasks.md             # Phase 2 output (Generated by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-813-llmxive-follow-up-extending-mint-managed/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py              # Configuration, seeds, limits
│   ├── data_generation/
│   │   ├── __init__.py
│   │   ├── synthetic_adapters.py  # FR-001, FR-002
│   │   ├── overlap_graph.py       # FR-002
│   │   └── request_trace.py       # FR-001 (Trace with topology coupling)
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── environment.py         # FR-003 (SimPy setup)
│   │   ├── policies/
│   │   │   ├── __init__.py
│   │   │   ├── fcfs.py            # FR-004
│   │   │   ├── greedy.py          # FR-004
│   │   │   └── topological.py     # FR-004
│   │   └── cost_model.py          # FR-009 (Calibrated to PCIe/DDR benchmarks)
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── statistics.py          # FR-006 (Shapiro-Wilk, t-test, Wilcoxon)
│   │   └── sensitivity.py         # FR-008 (Correlation sweep)
│   └── main.py                # Entry point
├── data/
│   ├── raw/                   # Generated synthetic adapters (sparse)
│   ├── processed/             # Topology graph, request traces (with coupling params)
│   └── results/               # Simulation logs, statistical outputs
├── tests/
│   ├── contract/              # Schema validation tests
│   ├── integration/           # End-to-end simulation tests
│   └── unit/                  # Unit tests for policies and graph logic
└── docs/
    └── paper/                 # Draft manuscript (generated from results)
```

**Structure Decision**: Selected a modular `code/` structure separating data generation, simulation logic, and analysis to ensure testability and adherence to the single source of truth. The `data/` directory strictly separates raw synthetic generation from processed results.

## Complexity & Feasibility Analysis

> **Critical Feasibility Check**: 10 replications × 3 policies × 100k requests = 3M events.
> **Strategy**:
> 1.  **Graph Lookup**: Pre-compute adjacency lists from the sparse matrix. Lookup is O(1) average per request, avoiding O(N) matrix scans.
> 2.  **Trace Sampling**: For multiple replications, use a request sample (100k) to ensure the time limit is met. A separate "Full Trace" run (1M) will be performed once per policy for the final paper figures (visualization only, not for statistical testing).
> 3.  **Memory**: Sparse matrix (CSR) for 10k nodes is <1GB. Simulation state is minimal.
> 4.  **Timeout**: The `main.py` entry point includes a `signal` handler to gracefully terminate and save partial results if the 6h limit is approached.

### Algorithmic Complexity & Optimization
*   **Graph Construction**: O(N^2 * K) where N=adapters, K=sparsity. With N=10,000 and K=0.01, this is ~10^6 operations, feasible in <5 mins.
*   **Simulation Loop**: O(1) per request using pre-computed adjacency lists. A large volume of requests per replication is trivial for SimPy on 2 vCPU.
*   **Total Runtime**: 10 replications × 3 policies × (100k requests + overhead) ≈ 3M events. Estimated runtime: within the 6-hour limit on GitHub Actions.

### Cost Model Calibration (FR-009)
The simulation cost model is calibrated against **published industry-standard benchmarks** for similar hardware, as "MinT" specific benchmarks are hypothetical:
*   **I/O Bandwidth**: **32 GB/s** (PCIe 4.0 x16) as per **Intel Xeon Platinum 8380** datasheet.
*   **Memory Copy**: **25 GB/s** (DDR4-3200) as per **Intel Xeon Platinum 8380** memory controller specs.
*   **Latency Calculation**: $Latency = \frac{\text{Adapter Size (MB)}}{\text{Bandwidth (MB/s)}} + \text{Fixed Overhead (0.5ms)}$.
This ensures that "latency" metrics are in meaningful milliseconds, not arbitrary units.

## Constitution Check (Detailed)

*   **FR-009 (Cost Model)**: `code/simulation/cost_model.py` will use hardcoded values derived from **Intel Xeon Platinum 8380** (PCIe 4.0 bandwidth ~32GB/s) and **DDR4-3200** memory copy benchmarks (~25GB/s). These values are documented in `code/config.py` and cited in `research.md`.
*   **FR-006 (Statistics)**: `code/analysis/statistics.py` implements the full pipeline:
    1.  Load results from 10 replications.
    2.  Compute difference vectors (Topological - FCFS).
    3.  Run `scipy.stats.shapiro` on differences.
    4.  Select `ttest_rel` or `wilcoxon` based on p-value > 0.05.
    5.  Output p-value and confidence intervals.

## Project Structure (Contracts)

The `contracts/` directory contains the following schema files, which define the strict validation rules for all generated data:
- `contracts/adapter.schema.yaml`: Structure of synthetic LoRA adapters.
- `contracts/request_trace.schema.yaml`: Structure of the request trace (including `topology_bias` field).
- `contracts/simulation-result.schema.yaml`: Structure of the aggregated simulation metrics.
- `contracts/topology-graph-schema.schema.yaml`: Structure of the overlap graph.

These schemas are used by `tests/contract/` to validate data integrity before simulation runs.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Sparse Matrix Representation** | [deferred] adapters with pairwise overlap creates a dense matrix whose dimensions scale with the number of adapters, resulting in substantial memory usage and significant calculation overhead. | A dense matrix approach risks out-of-memory (OOM) errors during calculation and storage on systems with constrained RAM. Sparse representation (CSR) is mandatory for feasibility. |
| **Discrete-Event Simulation (SimPy)** | Real hardware simulation is impossible on CPU-only CI; a cost model is required. | A simple loop-based "step" simulation lacks the precise event ordering and timing granularity needed to model eviction latency and I/O contention accurately. |
| **Statistical Bootstrapping/Replications** | Single run results are noisy; variance in request traces can mask policy improvements. | A single run cannot provide the statistical power required to claim p < 0.05 significance for the [deferred] reduction target. |
| **Correlated Trace Generation** | Without correlating access patterns to parameter overlap, the Topological policy has no signal to exploit. | A purely random trace would make the Topological policy's success a tautology of the data generation, not a test of the algorithm. |
| **100k vs 1M Trace Strategy** | 10 replications of 1M requests would exceed the 6-hour limit. | Using a sufficiently large number of samples for the statistical test and a larger set for visualization balances statistical power with compute feasibility. |