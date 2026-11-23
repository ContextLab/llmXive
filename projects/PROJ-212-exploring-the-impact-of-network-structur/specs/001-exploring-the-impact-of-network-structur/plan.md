# Implementation Plan: Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems

**Branch**: `001-network-synchronization-impact` | **Date**: 2026-06-14 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-network-synchronization-impact/spec.md`

## Summary

This project implements a computational pipeline to investigate the relationship between static network topology (degree distribution, clustering coefficient, average path length) and the synchronization robustness threshold of Kuramoto oscillator systems. The pipeline ingests network graphs, computes topological metrics using NetworkX, simulates Kuramoto dynamics via RK45 integration to find the critical coupling strength, and performs rigorous statistical regression (linear/polynomial) with cross-validation and multicollinearity checks. The implementation adheres to the strict CPU-first compute constraints of the GitHub Actions free tier, prioritizing data streaming and scalable algorithms where necessary.

Key revisions in this plan:
1.  **Threshold Precision**: Replaced discrete K-sweep with bisection search to minimize quantization error.
2.  **Network Reduction**: Defined BFS-based subgraph extraction for networks > 200 nodes.
3.  **Data Sources**: Corrected dataset URLs to verified SNAP and Network Repository sources.
4.  **Statistical Logic**: Explicitly implemented Spec FR-005 (LOOCV vs 10-fold) and resolved Constitution conflicts by prioritizing Spec requirements for small datasets.
5.  **No Synthetic Data**: Removed synthetic augmentation; strictly follows FR-004 (warning if N < 10).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx`, `scipy`, `numpy`, `pandas`, `scikit-learn`, `matplotlib`, `pytest`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results`)  
**Testing**: `pytest` with TDD workflow (tests written before implementation)  
**Target Platform**: Linux (GitHub Actions free tier: vCPU, ~7 GB RAM)  
**Project Type**: Scientific computing CLI / Data analysis pipeline  
**Performance Goals**: Complete pipeline for 10+ networks within 6 hours; single network simulation < 20 mins.  
**Constraints**: No local GPU; memory usage < 7 GB; strict adherence to spec-defined predictors (no unauthorized motif analysis).  
**Scale/Scope**: Variable dataset size; fallback to descriptive statistics if N < 10.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: The plan mandates pinned `requirements.txt`, random seed management in `src/simulation.py` (fixed seed for ω_i), and checksumming of all raw data in `data/raw`. The `main.py` orchestration will be deterministic.
- **Principle II (Verified Accuracy)**: All citations of datasets in `research.md` strictly reference the verified URLs provided in the project input (SNAP, Network Repository). No fabricated URLs.
- **Principle III (Data Hygiene)**: Raw data will be downloaded and checksummed. Derived metrics (`data/processed_metrics.csv`) will be generated via scripts, never manually edited.
- **Principle IV (Single Source of Truth)**: Regression results in `results/regression_summary.json` will be the sole source for paper statistics.
- **Principle V (Versioning)**: All artifacts (code, data, results) will be tracked with content hashes in the project state file.
- **Principle VI (Numerical Stability)**: The Kuramoto implementation will strictly use `scipy.integrate.ode` with `method='dop5'` (RK45) and fixed tolerances (`rtol=1e-6`, `atol=1e-9`). Initial phases will be seeded via `numpy.random.seed`.
- **Principle VII (Statistical Rigor)**: The plan enforces VIF checks (threshold > 5) and conditional regression logic (N < 10 warning). Cross-validation strategy (LOOCV for N<50, 10-fold for N≥50) will be implemented exactly as per FR-005, overriding any prior plan text suggesting 5x5-CV. The plan explicitly reports % confidence intervals and validates against the R² > 0.6 threshold as required, while acknowledging power limitations if N < 30.

## Project Structure

### Documentation (this feature)

```text
specs/001-network-synchronization-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── loader.py            # Data ingestion (Matrix Market, edge lists)
├── topology.py          # Metric computation (degree, clustering, path length)
├── simulation.py        # Kuramoto RK45 integration and threshold detection
├── stats.py             # Regression, VIF, Cross-validation
├── viz.py               # Heatmaps and diagnostic plots
├── utils.py             # Logging, seed management, file I/O helpers
├── validators.py        # Schema validation for inputs/outputs
└── main.py              # Orchestration script

data/
├── raw/                 # Original network files (.mtx, .csv)
├── processed/           # Computed metrics (.csv)
└── checksums.txt        # SHA256 hashes of raw data

results/
├── sim_results.json     # Per-network simulation outputs
├── regression_summary.json # Statistical analysis results
├── cv_report.json       # Cross-validation metrics
├── verification_report.json # SC-003 manual verification log
├── pipeline_status.json # Timeout/Success status
└── figures/             # Generated PNGs

tests/
├── __init__.py
├── test_loader.py
├── test_topology.py
├── test_simulation.py
├── test_stats.py
└── test_viz.py
```

**Structure Decision**: Single-project structure selected to minimize overhead for a scientific pipeline. All logic resides in `src/` with clear separation of concerns (loading, topology, simulation, stats, viz). The `contracts/` directory contains schemas used by `src/validators.py` for runtime validation of all output JSONs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Conditional CV Logic (LOOCV vs 10-fold) | Spec FR-005 mandates different strategies for N<50 vs N>=50 to balance bias/variance. This overrides the Constitution's general "10-fold" rule for this specific implementation. | A fixed CV method would violate the Spec's statistical rigor requirement for small datasets. |
| VIF Check & Ridge Fallback | Spec FR-006 requires handling multicollinearity to prevent invalid regression coefficients. | Ignoring collinearity would produce scientifically invalid results (spurious correlations). |
| Disconnected Graph Handling | Spec FR-002/FR-001 requires explicit handling of infinite path length and synchronization impossibility. Disconnected graphs are excluded from regression to avoid bias. | Assuming connectivity would crash the simulation or produce incorrect "synchronized" flags for disconnected components. |
| Bisection Search for Threshold | Discrete sweep (step=0.1) introduces quantization error that attenuates correlations. Bisection reduces error to <0.001. | Discrete sweep is insufficient for detecting effects in small samples (N<30). |
| BFS Subgraph Extraction | Networks vary in size (N=200 to N=millions). Random truncation destroys topology. BFS preserves local structure. | Random truncation or edge thinning alters density and synchronization thresholds independently of original topology. |
| Timeout Logging | SC-004 requires logging the specific network ID causing a timeout. | Generic timeout logging does not identify the bottleneck network. |
| No Synthetic Data | Spec Assumptions and FR-004 require real data. Synthetic augmentation is explicitly forbidden. | Synthetic data would invalidate the scientific claim about real-world network structures. |

## Data & Compute Feasibility

- **CPU-First**: All simulations (RK45) and statistical models (scikit-learn) are computationally lightweight for N=200 oscillators and typical network sizes (up to 10k nodes). No GPU is required.
- **Memory**: Streaming the dataset and processing one graph at a time ensures RAM usage remains well under the system memory limit..
- **Time**: With a A time limit is imposed., we can process a small to moderate number of networks (assuming Approximately a quarter of an hour per network). If the verified dataset yields more, we will process the initial subset. If the pipeline exceeds 6 hours, `results/pipeline_status.json` will log the specific network ID causing the delay.
- **Data Sources**: Verified URLs for SNAP and Network Repository are used. If these fail to yield graphs, the pipeline halts with a warning.