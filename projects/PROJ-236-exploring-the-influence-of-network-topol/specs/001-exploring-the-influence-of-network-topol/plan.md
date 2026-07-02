# Implementation Plan: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

**Branch**: `001-gene-regulation` | **Date**: 2024-05-21 | **Spec**: `specs/001-exploring-the-influence-of-network-topol/spec.md`
**Input**: Feature specification from `/specs/001-exploring-the-influence-of-network-topol/spec.md`

## Summary

This project investigates the correlation between atomic connectivity network topology (Small-World, Scale-Free, Random) and thermal conductivity in disordered materials. The technical approach involves: (1) generating reproducible network ensembles from atomic coordinates using distance-based cutoffs; (2) computing effective thermal conductivity via **Harmonic Lattice Dynamics (HLA) with mass disorder** using a Green-Kubo solver (CPU-tractable approximation to anharmonic dynamics); (3) performing statistical regression with bootstrap resampling and multiple-comparison corrections to identify topology-transport associations. The implementation strictly adheres to CPU-only constraints (2 cores, 7GB RAM) and avoids causal language.

**Critical Methodology Update**: Previous proposals using a simplified EMA (τ ∝ 1/metrics) were rejected as circular. The current plan uses a physics-based Green-Kubo solver where thermal conductivity emerges from mass disorder and bond stiffness, independent of topological metrics.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx` (graph generation/metrics), `scikit-learn` (regression/bootstrap), `numpy`/`scipy` (linear algebra, Green-Kubo integration), `pandas` (data handling), `matplotlib`/`seaborn` (visualization).  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/results`); JSON/CSV/Parquet formats.  
**Testing**: `pytest` (unit/integration), `pytest-cov` (coverage), `jsonschema` (contract validation).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7GB RAM).  
**Project Type**: Computational research pipeline (CLI-driven).  
**Performance Goals**: Full ensemble (100 realizations x 3 topologies) < 6 hours; individual realization < 45 minutes.  
**Constraints**: No GPU/CUDA; no large-LLM inference; memory < 7GB; strict reproducibility (fixed seeds).  
**Scale/Scope**: ~ network realizations; A large ensemble of atoms per realization (simulated).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Action |
|-----------|--------|-----------------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/config.yaml`; `requirements.txt` pinned; data checksums recorded. |
| **II. Verified Accuracy** | PASS | All dataset references in `research.md` point to verified URLs (Zenodo/HuggingFace) or standard loaders; no fabricated metrics. |
| **III. Data Hygiene** | PASS | `data/` structure enforces raw vs. processed separation; checksums in `state.yaml`. |
| **IV. Single Source of Truth** | PASS | All figures/stats derived from `data/results` via `code/analysis.py`; no hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | PASS | Content hashes for artifacts; `updated_at` timestamps managed by agent. |
| **VI. Numerical Stability** | PASS | `simulation_config.yaml` defines convergence criteria; fallback logic for non-convergent runs (a limited number of retries). |
| **VII. Network Construction Transparency** | PASS | Cutoffs, algorithms, and seeds stored in `data/metadata.json` for every graph. |

## Project Structure

### Documentation (this feature)

```text
specs/001-exploring-the-influence-of-network-topol/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── network.schema.yaml
│   ├── transport_result.schema.yaml
│   └── analysis_schema.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-236-exploring-the-influence-of-network-topol/
├── code/
│   ├── __init__.py
│   ├── config.py          # Loads config.yaml
│   ├── generate_networks.py # US-1: Network generation
│   ├── compute_transport.py # US-2: Transport calculation (HLA Green-Kubo)
│   ├── analyze_correlations.py # US-3: Regression & Bootstrap
│   └── utils.py           # Logging, checksums, retry logic
├── data/
│   ├── raw/               # Input atomic coordinates (or generated seeds)
│   ├── processed/         # Generated graphs, force constants
│   └── results/           # Conductivity values, regression stats
├── tests/
│   ├── test_networks.py
│   ├── test_transport.py
│   └── test_analysis.py
├── requirements.txt
└── simulation_config.yaml
```

**Structure Decision**: Single project structure selected. The research pipeline is linear (Generate -> Compute -> Analyze), and a single `code/` directory simplifies dependency management and testing for a CPU-bound scientific workflow.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed. | N/A |

## FR/SC Coverage Mapping

| FR/SC ID | Requirement | Plan Element Addressing It |
|----------|-------------|----------------------------|
| **FR-001** | Generate connected networks ([deferred] success) | `generate_networks.py`: Retry logic with cutoff sweep; logs exclusion reasons. |
| **FR-002** | CPU-only transport calc (<45m) | `compute_transport.py`: Uses Harmonic Lattice Dynamics (HLA) with mass disorder via Green-Kubo; timeout enforcement. |
| **FR-003** | Extract topological metrics | `generate_networks.py`: Computes path length, clustering, degree variance, spectral gap, betweenness. |
| **FR-004** | Bootstrap resampling (sufficient iterations for convergence) | `analyze_correlations.py`: `sklearn.utils.resample` with `n_bootstraps=1000`. |
| **FR-005** | Multiple-comparison correction | `analyze_correlations.py`: `statsmodels.stats.multitest.multipletests` (FDR/Bonferroni). |
| **FR-006** | Derive force constants if missing | `compute_transport.py`: Uses bond-distance based estimation (Lennard-Jones-like) for force constants. |
| **FR-007** | Associational framing only | `analyze_correlations.py`: Output strings explicitly use "correlation" / "association", no causal verbs. |
| **FR-008** | Sensitivity analysis on cutoff | `generate_networks.py`: Outer loop sweeps cutoff (1.0x to 2.0x) and aggregates results. |
| **SC-001** | ≥95% valid realizations | `generate_networks.py`: Assertion check; failure triggers warning and exclusion logging. |
| **SC-002** | Runtime < 6h total | `compute_transport.py`: Parallelization over 2 cores; timeout per realization. |
| **SC-003** | p < 0.05 after correction | `analyze_correlations.py`: Reports corrected p-values; threshold check in summary. |
| **SC-004** | CI width ≤ 0.2 | `analyze_correlations.py`: Calculates CI width (`ci_upper - ci_lower`) and stores it as `ci_width` in the output JSON to verify against the target. |
| **SC-005** | Report R² for power-law fit | `analyze_correlations.py`: Fits a power-law model (log-log regression) between network disorder parameters and conductivity reduction; reports the R² of this specific fit. The hypothesis is tested against a null of no correlation; the system does not guarantee R² ≥ 0.6. |

## Output Schema Consistency

The `analysis_schema.schema.yaml` is the source of truth for the `data/results/correlation_analysis.json` output. It explicitly includes `ci_width` (derived from `ci_upper` and `ci_lower`) and `r_squared` (specifically for the power-law fit) to match the requirements in `data-model.md` and the Success Criteria.