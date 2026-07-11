# Implementation Plan: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

**Branch**: `001-lrmxive-lora-topology-scheduling` | **Date**: 2026-07-05 | **Spec**: `specs/001-lrmxive-follow-up-extending-mint-managed/spec.md`
**Input**: Feature specification from `/specs/001-lrmxive-lora-topology-scheduling/spec.md`

## Summary

This project extends the "MinT" infrastructure concept by implementing a discrete-event simulation (DES) to optimize multi-tenant LLM serving. The core innovation is a "Topological Lookahead" scheduling policy that leverages a "LoRA Topology Graph" constructed from pairwise parameter overlap (cosine similarity) of synthetic LoRA adapters. The system generates a synthetic dataset of 10,000 adapters organized into K=50 distinct clusters to ensure a non-trivial, sparse graph structure. It simulates request traces generated via a Clustered Markov Chain under three policies (FCFS, Greedy Frequency, Topological Lookahead) to measure cold-start latency reductions. The implementation is strictly constrained to CPU-only execution (GitHub Actions free-tier: limited vCPU and RAM) using Python, SimPy, NumPy, and SciPy.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `simpy`, `numpy`, `scipy`, `networkx`, `pandas`, `pytest`, `hypothesis`  
**Storage**: Local filesystem (CSV/JSON/Parquet) for synthetic data and simulation logs; no external DB.  
**Testing**: `pytest` for unit tests (data generation, graph construction), integration tests (simulation runs), and statistical validation scripts.  
**Target Platform**: Linux (GitHub Actions Free Runner)  
**Project Type**: Research Simulation / CLI Tool  
**Performance Goals**: Simulation of 10^6 requests across 30 replications must complete in < 6 hours on 2 vCPU. Memory usage < 7 GB.  
**Constraints**: No GPU; no 8-bit/4-bit quantization libraries; all matrix operations must be CPU-tractable (sparse matrix formats used for efficiency, but logic remains strictly graph-based).  
**Scale/Scope**: A large set of synthetic LoRA adapters (Clustered); A large-scale request trace per replication

The research question, method, and references remain unchanged as no specific empirical values were asserted for them in the original passage beyond the quantity to be generalized.; Multiple independent replications per policy.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/simulation/run_experiment.py` and `code/data/generate_adapters.py`. `requirements.txt` pins exact versions. No external non-deterministic data sources. |
| **II. Verified Accuracy** | **PASS** | Citations to "MinT" paper and LoRA methodology will be verified by Reference-Validator. No fabricated URLs in `research.md`. |
| **III. Data Hygiene** | **PASS** | Synthetic data generation produces checksums recorded in `state/`. Raw generated artifacts are immutable; derived graphs are new files. |
| **IV. Single Source of Truth** | **PASS** | All metrics (latency, evictions) are extracted programmatically from simulation logs (`data/logs/`) and aggregated in `code/analysis/`. No hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | **PASS** | Content hashes for data and code will be computed by the Advancement-Evaluator. `state.yaml` updated on artifact change. |
| **VI. Simulation Validity** | **PASS** | DES implemented strictly in SimPy. Time units are abstract but consistent. Memory limits enforced via `MemoryLimitExceeded` events. **Determinism**: A substantial adapter count and a large request trace size are pinned in `code/data/generate_adapters.py` and `code/data/generate_trace.py` respectively. Seeds are fixed per replication to ensure exact reproducibility of the multiple replications. |
| **VII. Topological Signal Grounding** | **PASS** | Topological Lookahead policy uses *only* the `overlap_matrix` derived from the synthetic adapters. **Note**: Sparsity optimizations (e.g., using `scipy.sparse`) are computational implementation details to fit memory; they do not replace the graph logic with generic heuristics. The policy logic remains strictly dependent on the overlap values. |

## Project Structure

### Documentation (this feature)

```text
specs/001-lrmxive-lora-topology-scheduling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-813-llmxive-follow-up-extending-mint-managed/
├── code/
│   ├── data/
│   │   ├── generate_adapters.py       # FR-001: Synthetic LoRA generation (Clustered)
│   │   ├── generate_trace.py          # FR-001: Request trace generation (Clustered Markov)
│   │   └── compute_overlap.py         # FR-002: Overlap matrix & graph construction
│   ├── simulation/
│   │   ├── engine.py                  # FR-003: SimPy DES core (memory, jitter, delta loading)
│   │   ├── policies.py                # FR-004: FCFS, Greedy, Topological Lookahead
│   │   ├── run_simulation.py          # FR-005: Single trace execution
│   │   └── run_experiment.py          # FR-005: Orchestrator for 30 replications & 3 policies
│   ├── analysis/
│   │   ├── stats.py                   # FR-006: Paired t-test on replication means
│   │   └── visualize.py               # SC-001, SC-002: Plotting results
│   └── main.py                        # Entry point for CLI
├── data/
│   ├── raw/                           # Generated adapters (checksummed)
│   ├── processed/                     # Overlap matrix, graphs, traces
│   └── logs/                          # Simulation run logs
├── tests/
│   ├── unit/
│   │   ├── test_data_gen.py
│   │   └── test_graph.py
│   ├── integration/
│   │   └── test_simulation_flow.py
│   └── contract/
│       └── test_schema_validation.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to minimize overhead. `code/` is organized by functional domain (data, simulation, analysis) to align with the linear flow of the research pipeline: Generate -> Model -> Analyze. This ensures data is generated before simulation, and simulation logs are generated before analysis, satisfying the computational task ordering requirement.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Clustered Data Generation** | Required to create a non-trivial topology graph (sparse clusters vs. dense clique). | A uniform random generation or "star topology" would result in a graph where all nodes are equally similar, making the Topological policy indistinguishable from random. |
| **Delta Loading Mechanism** | Required to model the physical benefit of overlap (reduced data transfer). | A constant load time model would only measure cache hit rates, failing to capture the "cold-start latency reduction" hypothesis. |
| **Paired Statistical Design** | Required to isolate the policy effect from trace variance. | An unpaired design would introduce trace variance into the error term, reducing statistical power. |
| **30 Independent Replications** | Required for statistical power (SC-003) to detect a [deferred] improvement with p < 0.05. | Single run or 5 replications would yield high variance and inconclusive p-values. |
| **Discrete-Event Simulation (SimPy)** | Necessary to model stochastic jitter (±10%) and memory constraints accurately. | A simple loop or analytical model cannot capture the dynamic cache eviction and memory overflow events realistically. |

