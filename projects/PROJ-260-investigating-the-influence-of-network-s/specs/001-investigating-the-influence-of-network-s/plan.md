# Implementation Plan: Investigating the Influence of Network Structure on Heat Conduction in Amorphous Solids

**Branch**: `001-investigate-network-heat-conduction` | **Date**: 2024-05-21 | **Spec**: `specs/001-investigate-network-heat-conduction/spec.md`
**Input**: Feature specification from `/specs/001-investigate-network-heat-conduction/spec.md`

## Summary

This project implements a computational pipeline to investigate the correlation between network topology (coordination numbers, bond angle variance, bottleneck density) and thermal conductivity in amorphous silicon. The system parses MD trajectories (LAMMPS/XYZ), constructs bond networks based on the Radial Distribution Function (RDF) minimum, computes Vibrational Density of States (VDOS) and participation ratios, and performs robust statistical correlation analysis (Spearman/Pearson with Bootstrap) across **multiple independent disorder realizations** (N≥30 snapshots) per system size. This design ensures statistical validity and decouples system size effects from topological disorder. The implementation adheres to a CPU-first compute strategy, ensuring feasibility on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `scikit-learn`, `ase` (Atomic Simulation Environment), `matplotlib`, `seaborn`, `networkx`  
**Storage**: Local filesystem (`data/`, `code/`, `outputs/`); CSV/Parquet for intermediate results.  
**Testing**: `pytest` with `pytest-cov` for coverage; `pytest-randomly` for reproducibility checks.  
**Target Platform**: Linux (GitHub Actions runner: CPU, ~7 GB RAM).  
**Project Type**: CLI / Data Analysis Pipeline.  
**Performance Goals**: Full pipeline (Topology + VDOS + Correlation) for a -atom system ≤ 30 minutes on 4-core CPU (SC-005).  
**Constraints**: No GPU usage; memory footprint ≤ 7 GB; strict reproducibility via pinned seeds; no synthetic data generation (real trajectories + programmatic reference generation).  
**Scale/Scope**: Multiple system sizes (N=, 2000, 4000) with ≥30 independent disorder realizations each; A substantial number of bootstrap iterations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Strategy |
|-----------|-------------------|-------------------------|
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. External datasets fetched via deterministic URLs. `requirements.txt` pins versions. Reference values generated programmatically, not manually. |
| **II. Verified Accuracy** | **PASS** | All dataset citations in `research.md` restricted to the "Verified datasets" block provided by the system. The **Reference-Validator Agent** will run on every artifact write to verify citations against primary sources (Constitution Verified Accuracy Gate). |
| **III. Data Hygiene** | **PASS** | Raw data files will be checksummed upon download. Derivations (topology, VDOS) written to new files with derivation logs. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `quickstart.md` and final reports will be generated programmatically from `data/` artifacts, not hand-typed. |
| **V. Versioning Discipline** | **PASS** | A dedicated `scripts/update_state_hashes.py` will compute `sha256` of all artifacts and update the project state YAML file automatically after each run. |
| **VI. Computational Numerical Stability** | **PASS** | VDOS and RDF calculations will use `numpy.float64`. Tolerance thresholds for RDF minima will be explicitly documented and logged. |
| **VII. Network Topology Extraction Consistency** | **PASS** | Bond networks will be constructed using a dataset-specific RDF minimum cutoff, not a global fixed value, to prevent systematic bias. |

## Project Structure

*Note: `contracts/` are Phase 1 outputs that serve as inputs to this Phase 2 plan.*

### Documentation (this feature)

```text
specs/001-investigating-the-influence-of-network-s/
├── plan.md              # This file (Phase 2)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Inputs to Plan)
│   ├── topology.schema.yaml
│   ├── vdos.schema.yaml
│   └── correlation.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── __init__.py
│   ├── simulation_box.py      # Data class for MD box metadata
│   ├── bond_network.py        # Graph representation logic
│   └── vibrational_spectrum.py # VDOS calculation logic
├── services/
│   ├── __init__.py
│   ├── topology_extractor.py  # FR-001, FR-002 implementation (uses `ase` as the only allowed parser)
│   ├── vdos_calculator.py     # FR-003, FR-004 implementation
│   ├── statistical_analyzer.py # FR-005, FR-006, FR-007 implementation
│   ├── reference_generator.py # NEW: Generates independent κ values (FR-008)
│   └── sensitivity_analyzer.py # NEW: Threshold sweep (US-2)
├── cli/
│   ├── __init__.py
│   └── main.py                # Entry point for pipeline execution
└── lib/
    ├── utils.py               # Helper functions (checksums, logging)
    └── config.py              # Configuration and seed management

tests/
├── contract/
│   ├── test_topology_schema.py
│   ├── test_vdos_schema.py
│   └── test_correlation_schema.py
├── integration/
│   ├── test_full_pipeline.py
│   └── test_runtime_threshold.py  # NEW: SC-005 runtime check
└── unit/
    ├── test_rdf.py
    ├── test_bond_network.py
    ├── test_bootstrap.py
    └── test_independence_check.py # NEW: FR-008 logic

data/
├── raw/                       # Downloaded trajectories (checksummed)
├── derived/
│   ├── topology/              # CSVs of coordination/bond angles
│   ├── vdos/                  # CSVs of VDOS and participation ratios
│   ├── reference/             # Programmatic κ estimates
│   └── correlation/           # Final correlation results
└── metadata/                  # (Removed manual CSV; replaced by programmatic generation)

outputs/
├── figures/                   # Generated plots
└── reports/                   # PDF/HTML summaries
```

**Structure Decision**: Selected Option 1 (Single Project) with a clear separation of `models` (data structures), `services` (business logic), and `cli` (entry point). This aligns with the need for a reproducible, modular pipeline where each functional requirement (FR) maps to a specific service module. The `tests/` directory mirrors this structure to ensure contract, integration, and unit coverage.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Bootstrap Resampling (iterations)** | Required by FR-005 and SC-001 to estimate 95% confidence intervals robustly on N≥30 samples. | Standard parametric tests (t-test) assume normality which may not hold for complex topological metrics; non-parametric bootstrap is safer. |
| **RDF-based Dynamic Cutoff** | Required by Constitution Principle VII to avoid systematic bias across different amorphous structures. | A fixed global cutoff (e.g., 2.5 Å) would fail to adapt to thermal expansion or structural variations, invalidating the correlation. |
| **Separate Topology and VDOS Services** | Allows independent testing and potential reuse of topology extraction if only structural metrics are needed. | A monolithic script would make unit testing of the VDOS calculation (which depends on velocities, not just topology) difficult. |
| **Reference Generator Service** | Required by FR-008 and Constitution Principle I to ensure κ values are independent and reproducible without manual CSVs. | Manual CSV entry violates reproducibility and introduces human error; using the same trajectory for κ and topology creates circular validation. |
| **Multiple Independent Snapshots (N≥30)** | Required to provide N≥30 for valid statistical inference, addressing the N=3 flaw. | Correlating only 3 system sizes (N=3) is statistically invalid and renders bootstrap meaningless. |
| **Sensitivity Analyzer Service** | Required by US-2 to sweep threshold and report stability. | Hardcoding a single threshold ignores the uncertainty in defining "under-coordinated" atoms. |
| **Runtime Threshold Test** | Required by SC-005 to ensure feasibility. | Without a specific test, the performance goal is unverified. |

## Implementation Phases

### Phase 1: Data Ingestion and Topology Extraction
*   **Input**: MD trajectory files (LAMMPS dump, XYZ).
*   **Action**: `topology_extractor.py` parses coordinates using `ase` (FR-001).
*   **Action**: Computes RDF, identifies first minimum for cutoff (Constitution VII).
*   **Action**: Constructs bond network and calculates metrics (FR-002).
*   **Output**: `data/derived/topology/` CSVs.

### Phase 2: Vibrational Analysis and Scattering
*   **Input**: Velocity data + Topology.
*   **Action**: `vdos_calculator.py` computes VACF and VDOS (FR-003).
*   **Action**: Calculates Participation Ratio and Mean Free Path estimates (Scientific Soundness).
*   **Action**: Identifies localized modes (FR-004).
*   **Output**: `data/derived/vdos/` CSVs.

### Phase 3: Reference Generation & Independence Check
*   **Input**: Simulation box metadata.
*   **Action**: `reference_generator.py` computes κ using Cahill-Pohl model or disjoint trajectory Green-Kubo (FR-008).
*   **Action**: **Independence Check**: Compares trajectory IDs. Halts if source is not independent (FR-008).
*   **Output**: `data/derived/reference/` CSVs.

### Phase 4: Sensitivity Analysis
*   **Input**: Topology metrics.
*   **Action**: `sensitivity_analyzer.py` sweeps under-coordination threshold (±0.5) (US-2).
*   **Action**: Reports coefficient of variation for bottleneck density.
*   **Output**: Sensitivity report.

### Phase 5: Statistical Correlation and Validation
*   **Input**: Topology, VDOS, κ, Sensitivity results.
*   **Action**: `statistical_analyzer.py` aggregates data (N≥30 per group).
*   **Action**: Performs Spearman/Pearson correlation within system size groups (Methodology).
*   **Action**: Bootstrap (iters) and Multiple Comparison Correction (FR-007).
*   **Action**: Power Analysis (SC-002).
*   **Action**: Runtime Measurement (SC-005).
*   **Output**: `data/derived/correlation/` results.

### Phase 6: Versioning and Reporting
*   **Action**: `scripts/update_state_hashes.py` computes SHA256 of all artifacts.
*   **Action**: Updates `state/projects/PROJ-260-...yaml` with hashes.
*   **Action**: Generates final report.