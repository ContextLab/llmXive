# Implementation Plan: The Impact of Bounded Confidence on Opinion Polarization Speed

**Branch**: `001-gene-regulation` | **Date**: 2026-07-13 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a computational study to determine how network topology (Erdős-Rényi, Barabási-Albert, Watts-Strogatz) disrupts the universal power-law scaling of convergence time in Bounded Confidence Models (Hegselmann-Krause). The approach involves generating synthetic network ensembles ($N=500$), executing discrete-time opinion dynamics simulations across a swept confidence threshold $\epsilon$ ranging from low to moderate values, and analyzing the resulting convergence times to extract scaling exponents $\gamma$ and test correlations with structural metrics (assortativity, path length).

Crucially, the analysis treats the extracted $\gamma$ as a *finite-size scaling exponent* for $N=500$, comparing relative differences across topologies rather than claiming absolute universality. The methodology employs a strictly non-circular, two-stage estimation procedure to avoid overfitting $\epsilon_c$.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx` (graph generation), `numpy` (numerical ops), `pandas` (data handling), `scikit-learn` (regression/fitting), `scipy` (curve fitting), `matplotlib` (visualization), `pytest` (testing).  
**Storage**: Local filesystem (`data/` for raw/processed data, `code/` for scripts). Checksums stored in `data/.checksums.json` and recorded in `state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml`.  
**Testing**: `pytest` with contract-based validation against `contracts/` schemas.  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, 7GB RAM, 14GB disk, no GPU).  
**Project Type**: Computational Research / CLI  
**Performance Goals**: Complete 1,500 simulations (topologies × 10 $\epsilon$ × 50 seeds) within 5 hours; RAM usage < 7GB.  
**Constraints**: No GPU usage; all heavy matrix ops must be vectorized NumPy; max iterations capped at [deferred] per run.
**Scale/Scope**: topologies, A range of epsilon values, seeds per config, $N=500$ nodes.

> Note: The "gene-regulation" branch name is retained from the spec header but the content is strictly opinion dynamics; this is a known artifact of the template pipeline.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan mandates pinning random seeds for network generation and simulation initialization. `requirements.txt` will pin exact versions.
- **Principle II (Verified Accuracy)**: Citations to literature (Hegselmann & Krause; Deffuant et al.) will be validated against primary sources **during the Research Phase (Phase 0)** via the Reference-Validator Agent, before the research artifact is finalized. This satisfies the Verified Accuracy Gate requirement.
- **Principle III (Data Hygiene)**: Raw simulation outputs will be written to `data/raw/` with checksums recorded in `data/.checksums.json`. Derived metrics (scaling exponents) written to `data/processed/`. No in-place modification.
- **Principle IV (Single Source of Truth)**: All figures and statistics in the final report will be generated programmatically from `data/processed/` via scripts in `code/`.
- **Principle V (Versioning Discipline)**: Artifacts will be hashed; the `state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml` file will be updated under the `artifact_hashes` key on every run, ensuring compliance with the Advancement-Evaluator checks.
- **Principle VI (Topological Robustness)**: Plan explicitly requires comparative analysis across Scale-Free (BA) and Small-World (WS) topologies to validate the divergence of $\gamma$.
- **Principle VII (Emergent Property Isolation)**: The code structure separates `network_generation.py` (structural metrics) from `simulation_engine.py` (temporal dynamics). Convergence time is recorded as an outcome, not an input.

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-672-the-impact-of-bounded-confidence-on-opin/
├── code/
│   ├── requirements.txt
│   ├── generate_networks.py       # FR-001: Network generation
│   ├── simulate_hk.py             # FR-002, FR-003, FR-004, FR-007: HK Simulation
│   ├── analyze_scaling.py         # FR-005, FR-006: Power-law fit & Regression
│   ├── sensitivity_analysis.py    # FR-008: Threshold sweep
│   ├── utils/
│   │   ├── metrics.py             # Structural metric calculation
│   │   ├── plotting.py            # Visualization
│   │   └── checksums.py           # Checksum generation for Principle III
│   └── main.py                    # Orchestration script
├── data/
│   ├── raw/                       # Raw simulation outputs (CSV/Parquet)
│   ├── processed/                 # Aggregated metrics and fitted parameters
│   └── .checksums.json            # SHA-256 hashes of all data files
├── tests/
│   ├── unit/
│   │   ├── test_network_gen.py
│   │   └── test_hk_logic.py
│   └── contract/
│       └── test_schemas.py
└── specs/001-gene-regulation/     # Specification artifacts
```

**Structure Decision**: Single `code/` directory with modular scripts. This minimizes overhead and fits the CLI nature of the research. The separation of `generate`, `simulate`, and `analyze` ensures that data flows linearly (downstream tasks depend on upstream artifacts), satisfying the computational task ordering requirement.

## Complexity Tracking

No complexity violations detected. The scope is tightly bounded by the GitHub Actions constraints (7GB RAM, 6h runtime), and the methodology (synthetic data, CPU-only) is explicitly designed to fit this box.

## Implementation Phases

### Phase 0: Research & Design
1.  **Literature Review & Citation Validation**: Validate citations for HK model and scaling laws (Principle II). Run Reference-Validator Agent on all citations before finalizing this research artifact.
2.  **Methodology Finalization**: Confirm two-stage estimation for $\epsilon_c$ (peak-finding) and per-instance regression strategy to avoid circularity and collinearity.
3.  **Data Model Definition**: Finalize schemas for `ScalingResult`, `SensitivityResult`, and `RegressionResult`.

### Phase 1: Implementation
1.  **Network Generation**: Implement `generate_networks.py` to produce multiple instances per topology.
2.  **Simulation Engine**: Implement `simulate_hk.py` with vectorized updates and convergence checks.
3.  **Analysis Pipeline**: Implement `analyze_scaling.py` with:
    *   Peak-finding for $\epsilon_c$ (independent of fit).
    *   Model comparison (Power-Law vs. Exponential) with AIC.
    *   Per-instance regression (N=150) with topology as a fixed effect.
4.  **Sensitivity Analysis**: Implement `sensitivity_analysis.py` for threshold robustness.
5.  **Checksum Generation**: Add `utils/checksums.py` to generate `data/.checksums.json` and update the state file.

### Phase 2: Validation & Reporting
1.  **Contract Testing**: Run `pytest` against JSON schemas.
2.  **State Update**: Update `state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml` with new artifact hashes under `artifact_hashes`.
3.  **Visualization**: Generate plots for $\gamma$ vs. structural metrics.
