# Implementation Plan: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

**Branch**: `001-gene-regulation` | **Date**: 2026-07-03 | **Spec**: `specs/001-exploring-the-influence-of-network-topol/spec.md`
**Input**: Feature specification from `specs/001-exploring-the-influence-of-network-topol/spec.md`

## Summary

This project investigates the associational correlation between atomic connectivity network topology (Small-World, Scale-Free, Random) and effective thermal conductivity in disordered materials. The technical approach involves generating reproducible network ensembles from disordered atomic coordinates, computing thermal conductivity via the **Allen-Feldman theory** (a CPU-tractable method for disordered systems that avoids third-order force constants), and performing statistical regression with ANOVA and bootstrap resampling to quantify topology-transport relationships.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `networkx`, `numpy`, `scipy`, `scikit-learn`, `pandas`, `matplotlib`, `seaborn`  
**Storage**: Local filesystem (`data/` for generated graphs and results, `code/` for scripts)  
**Testing**: `pytest` (unit tests for graph generation, integration tests for transport calculation)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7 GB RAM, no GPU)  
**Project Type**: Computational physics research pipeline  
**Performance Goals**: Total ensemble runtime ≤ 6 hours; individual realization ≤ 15 minutes (excluding pilot/sensitivity); memory footprint ≤ 7 GB  
**Constraints**: No GPU/CUDA; no deep learning training; no 8-bit quantization; strict CPU-only execution; all results must be real computations, not placeholders.  
**Scale/Scope**: A sufficient number of network realizations per ensemble type; system size ≤ 500 atoms (validated via finite-size scaling pilot).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: All random seeds will be pinned in `code/`. External datasets (if any) will be fetched from canonical sources (HuggingFace/UCI) with checksums recorded.
- **Principle II (Verified Accuracy)**: All citations in `research.md` will be verified against primary sources (e.g., Allen & Feldman, [Year]). No fabricated URLs will be used.
- **Principle III (Data Hygiene)**: Generated data in `data/` will be checksummed. No in-place modifications; derivations produce new files.
- **Principle IV (Single Source of Truth)**: All figures/statistics in the final output will trace to specific rows in `data/` and code blocks in `code/`.
- **Principle V (Versioning Discipline)**: Content hashes will be tracked. **Stale artifacts will invalidate review records, and the `state/projects/PROJ-236-exploring-the-influence-of-network-topol.yaml` `updated_at` timestamp will be updated on every artifact change.**
- **Principle VI (Numerical Stability and Convergence)**: `simulation_config.yaml` will document convergence criteria. **Results must be demonstrated converged with respect to system size (via finite-size scaling pilot) and ensemble size (≥ 100 realizations), as described in the Methodology sketch.**
- **Principle VII (Network Construction Transparency)**: Cutoff parameters, algorithms, and seeds will be stored in `data/` alongside graph files.

## Project Structure

### Documentation (this feature)

```text
specs/001-exploring-the-influence-of-network-topol/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── network_realization.schema.yaml
│   ├── transport_schema.schema.yaml
│   └── analysis_schema.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-236-exploring-the-influence-of-network-topol/
├── code/
│   ├── requirements.txt
│   ├── 01_generate_networks.py
│   ├── 02_compute_transport.py
│   ├── 03_analyze_correlations.py
│   └── simulation_config.yaml
├── data/
│   ├── raw/             # Atomic coordinates (if external)
│   ├── processed/       # Generated graphs, force constants, conductivity results
│   └── checksums.txt
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: Single project structure selected. This is a linear research pipeline (Generate → Simulate → Analyze) best served by a monolithic codebase with modular scripts. No frontend/backend split is required.

## Complexity Tracking

No violations detected. The single-project structure minimizes overhead and aligns with the linear workflow of the research.

## Unresolved panel concerns (addressed in this revision)

The previous iteration was rejected due to a **FABRICATED-RESULT** signal and multiple **methodology** concerns.

- **Resolution for FABRICATED-RESULT**: This plan strictly prohibits placeholders. All numerical results in `research.md` and `data-model.md` will be derived from actual code execution on the GitHub Actions runner using the Allen-Feldman method. The `research.md` section "Dataset Strategy" explicitly states that *no external pre-computed results* are used.
- **Resolution for Methodology**: Replaced the infeasible `phono3py` and undefined "simplified models" with the **Allen-Feldman theory** (Allen & Feldman, 1989), which is CPU-tractable for N≤500 and valid for disordered systems. Force constants are derived from an EAM-like potential independent of the graph topology to prevent circular validation.
- **Resolution for Spec Coverage**: Added explicit phases for Sensitivity Analysis (FR-008), Finite-Size Scaling (FR-011/Regime Validation), and Power-Law Fitting (SC-005).
- **Resolution for Constitution**: Updated checks to explicitly reference Principle V's `updated_at` requirement and Principle VI's "Methodology sketch".
- **Resolution for File Naming**: Corrected `network_schema.schema.yaml` to `network_realization.schema.yaml` throughout.
- **Resolution for Computational Budget**: Sensitivity analysis is performed on a representative subset; Finite-Size Scaling is a one-time pilot.