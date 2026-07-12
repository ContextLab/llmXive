# Implementation Plan: llmXive follow-up: extending "MinT: Managed Infrastructure for Training and Serving Millions of LLMs"

**Branch**: `001-lora-topology-scheduling` | **Date**: 2026-07-05 | **Spec**: `specs/001-llmxive-follow-up-extending-mint-managed/spec.md`

## Summary

This project implements a CPU-tractable discrete-event simulation to evaluate a "Topological Lookahead" scheduling policy for LoRA adapter loading in the MinT infrastructure. The core innovation is constructing a "LoRA Topology Graph" based on pairwise parameter overlap of synthetic adapters and using this graph to prefetch adapters during request processing. The system replaces GPU-dependent training with a sparse-matrix-first synthetic data generator and a SimPy-based simulation engine, ensuring execution on GitHub Actions free-tier runners (limited vCPU, limited RAM, no GPU). The plan strictly adheres to the project constitution's requirements for reproducibility, statistical rigor (Wilcoxon signed-rank), and data hygiene.

**Critical Design Correction**: To ensure scientific validity, the Topology Graph (Adapters) is generated **ONCE** per experiment and remains **FIXED** across all 10 replications. Only the Request Trace is regenerated per seed. This isolates the policy effect from topology variance, addressing the confound identified in the review. (Note: FR-006 in the spec currently mandates "full dataset regeneration"; this plan implements the scientifically correct "Fixed Topology" design and flags FR-006 for a spec update).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `simpy`, `numpy`, `scipy`, `networkx`, `pandas`, `pytest`, `hypothesis`, `pyyaml`  
**Storage**: In-memory sparse matrices (CSR format), JSON/CSV logs, YAML schemas. No persistent database.  
**Testing**: `pytest` (unit, integration, contract tests), `hypothesis` (property-based testing for edge cases).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`), CPU-only.  
**Project Type**: Simulation / Research Tool  
**Performance Goals**: Complete 10^6 request trace simulation with 10 replications within 6 hours; peak RSS < 6GB.  
**Constraints**: No GPU/CUDA; no large-LLM inference; strict memory limits; deterministic seeds.  
**Scale/Scope**: Synthetic generation of a large-scale set of adapters; 10^6 request trace; 10 independent replications.

> Empirical values (exact adapter counts, latency numbers) are deferred to the implementation/research phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action/Note |
|-----------|--------|-------------|
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/utils/seeds.py`. `requirements.txt` pins exact versions. Simulation is deterministic given seed. |
| **II. Verified Accuracy** | **PASS** | Citations for cost model parameters (NVMe/DDR4 bandwidth) will be sourced from standard hardware benchmarks (e.g., Phoronix, Intel/AMD whitepapers) and verified by the Reference-Validator in Phase 0.5. |
| **III. Data Hygiene** | **PASS** | Synthetic data generation scripts output to `data/processed/`. Checksums recorded in `state/...yaml`. No PII possible (synthetic only). |
| **IV. Single Source of Truth** | **PASS** | All metrics in `docs/paper.md` will be derived directly from `data/processed/simulation_results.csv` via `code/analysis/report_generator.py`. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts managed by the state file. |
| **VI. Simulation Determinism** | **PASS** | SimPy environment configured with fixed seeds. Topology graph generation is independent of access trace (strict separation of concerns). |
| **VII. Statistical Rigor** | **PASS** | Plan mandates Wilcoxon signed-rank test (default) regardless of normality, with multiple independent replications (Fixed Topology, Regenerated Traces). |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-mint-managed/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── adapter.schema.yaml
│   ├── request_trace.schema.yaml
│   ├── simulation_result.schema.yaml
│   ├── topology-graph.schema.yaml
│   ├── simulation-event.schema.yaml
│   ├── policy-result.schema.yaml
│   └── overlap-metric.schema.yaml
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── generator.py       # Synthetic adapter & trace generation (FR-001, FR-011)
│   └── topology.py        # Overlap matrix construction (FR-002)
├── simulation/
│   ├── env.py             # SimPy environment setup (FR-003)
│   ├── policies.py        # FCFS, Greedy, Topological Lookahead (FR-004)
│   └── runner.py          # Simulation orchestration & timeout (FR-007, FR-014)
├── analysis/
│   ├── statistics.py      # Wilcoxon signed-rank (FR-006, SC-003)
│   └── metrics.py         # Latency, eviction, hit-rate calculation (FR-005, SC-001, SC-002)
├── utils/
│   ├── seeds.py           # Global seed management (Constitution I)
│   └── memory.py          # RSS monitoring & sparse fallback (FR-012)
└── cli/
    └── main.py            # Entry point for running experiments

tests/
├── contract/              # Schema validation tests
├── integration/           # End-to-end simulation tests
└── unit/                  # Policy logic tests

data/
├── raw/                   # (Empty, synthetic generation is code-driven)
├── processed/             # Generated topologies, traces, results
└── logs/                  # Simulation logs

docs/
└── paper.md               # Final report (derived from data)
```

**Structure Decision**: Single project structure (`code/`) is selected to minimize overhead and ensure tight coupling between generation, simulation, and analysis, which is critical for the 6-hour runtime constraint.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Sparse Matrix Strategy** | Required to fit a large-scale overlap matrix in limited RAM. | Dense float64 matrix would require ~800MB, but with overhead and trace storage, risk of OOM is high. CSR is mandatory for scalability. |
| **Three Policies** | Required to isolate the value of Topological Lookahead against FCFS (baseline) and Greedy (heuristic). | Two-policy comparison (Topo vs FCFS) would fail to prove improvement over standard frequency-based caching. |
| **Statistical Replications** | Required for Constitution Principle VII (Statistical Rigor). | Single-run comparison is statistically invalid due to simulation variance; p-values would be meaningless. |
| **Fixed Topology Design** | Required to isolate policy effect from topology variance. | Regenerating topology per seed (as in original FR-006) confounds policy performance with random graph structure. |

## Implementation Phases

### Phase 0: Environment & Cost Model Calibration (FR-009, Constitution II)
*   **Task 0.1**: Initialize project structure (verify `code/`, `data/`, `tests/`, `contracts/` directories exist).
*   **Task 0.2**: Install dependencies (`simpy`, `numpy`, `scipy`, `networkx`, `pandas`, `pytest`, `hypothesis`) from `requirements.txt`.
*   **Task 0.3**: Configure linting (ruff) and formatting (black) via `pyproject.toml`.
*   **Task 0.4**: **Calibrate Cost Model**: Retrieve standard CPU I/O bandwidth values (NVMe ~3.5 GB/s, DDR4 ~50 GB/s) from verified sources (e.g., Intel/AMD whitepapers). Store these constants in `code/simulation/config.py`.
*   **Task 0.5**: **Citation Validation**: Run Reference-Validator on the hardware benchmarks used in Task 0.4.

### Phase 0.2: Warm-up Verification (FR-010)
*   **Task 0.2.1**: Generate a small subset (e.g., 100 adapters, 10k requests).
*   **Task 0.2.2**: Run a single replication of all policies.
*   **Task 0.2.3**: Verify runtime < 5 minutes and memory < 2GB. If exceeded, adjust pruning threshold or subset size.

### Phase 1: Data Generation & Topology Construction (FR-001, FR-002, FR-012)
*   **Task 1.1**: Generate synthetic LoRA adapters (rank 1-256, random sparsity) and save to `data/processed/adapters.pkl`.
*   **Task 1.2**: Compute pairwise parameter overlap matrix (CSR format) and save to `data/processed/topology.pkl`.
*   **Task 1.3**: **Validate Topology**: Verify symmetry, no NaNs/Infs, and report graph density/overlap distribution (SC-008).
*   **Task 1.4**: **Freeze Topology**: Lock this topology for all subsequent replications.

### Phase 2: Trace Generation (FR-011)
*   **Task 2.1**: Implement Markov chain trace generator: $P(B|A) = \text{base} + k \times \text{Overlap}(A,B)$.
*   **Task 2.2**: Generate a large-scale set of request traces for each seed (multiple seeds).
*   **Task 2.3**: Generate **Control Traces**: One set with $k=0$ (random) and one with $k=-0.1$ (anti-correlated) for stress testing (FR-013).

### Phase 3: Simulation Execution (FR-003, FR-004, FR-005, FR-007, FR-014)
*   **Task 3.1**: Implement FCFS, Greedy, and Topological Lookahead policies.
*   **Task 3.2**: Run simulation for each policy, each seed, and each trace type (bias, random, anti-correlated).
*   **Task 3.3**: Log events (load, evict, process) and metrics (latency, evictions, memory).
*   **Task 3.4**: Enforce hard memory/time limits; terminate gracefully on timeout.

### Phase 4: Sensitivity Analysis (FR-008)
*   **Task 4.1**: Vary sparsity patterns (low, medium, high) in data generation.
*   **Task 4.2**: Re-run Phases 1-3 for each sparsity level.
*   **Task 4.3**: Compare Topological Lookahead performance across sparsity levels.

### Phase 5: Statistical Analysis & Reporting (FR-006, SC-001, SC-002, SC-003, SC-008)
*   **Task 5.1**: Aggregate results from multiple replications (Fixed Topology, Regenerated Traces).
*   **Task 5.2**: Perform Shapiro-Wilk test (diagnostic only).
*   **Task 5.3**: Perform **Wilcoxon signed-rank test** (default) on latency differences (Topo vs FCFS, Topo vs Greedy).
*   **Task 5.4**: Calculate p50 latency reduction, eviction reduction, and p-values.
*   **Task 5.5**: Generate final report and paper draft.

## Contracts & Schemas

The following canonical schema files define the data contracts:
- `contracts/adapter.schema.yaml`: LoRA Adapter entity.
- `contracts/request_trace.schema.yaml`: Request Trace entity.
- `contracts/simulation_result.schema.yaml`: Aggregated simulation metrics.
- `contracts/topology-graph.schema.yaml`: Topology graph metadata.
- `contracts/simulation-event.schema.yaml`: Individual simulation events.
- `contracts/policy-result.schema.yaml`: Policy-specific aggregation.
- `contracts/overlap-metric.schema.yaml`: Pairwise overlap metrics.

*Note: Duplicate/suffix variants (e.g., `adapter-schema.schema.yaml`) have been removed to ensure consistency.*

## Data Integrity & Reproducibility

- **No Fabricated Metrics**: All results must be computed by running the simulation. No hardcoded or placeholder values are allowed.
- **Seed Management**: `code/utils/seeds.py` manages all random seeds.
- **Checksums**: All generated data files are checksummed and recorded in `state/...yaml`.
- **Validation**: `tests/contract/test_schemas.py` validates all output against the canonical schemas.