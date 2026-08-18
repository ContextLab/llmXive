# Implementation Plan: Quantifying the Influence of Network Topology on Thermal Conductivity in Amorphous Silicon

**Branch**: `001-topology-thermal-conductivity` | **Date**: 2026-06-25 | **Spec**: `specs/001-quantifying-the-influence-of-network-top/spec.md`
**Input**: Feature specification from `/specs/001-quantifying-the-influence-of-network-top/spec.md`

## Summary

This project implements a computational pipeline to quantify the influence of network topology on thermal conductivity in amorphous silicon. The approach involves: (1) ingesting pre-equilibrated amorphous silicon configurations (XYZ) and constructing atomic graphs with a chemically relevant bond cutoff

Reference: None specified in passage.
Research Question: Not specified in passage.
Method: Constructing atomic graphs with a bond cutoff. using `ase` (FR-001); (2) extracting local topological metrics (degree, clustering, shortest-path) and computing ground-truth thermal conductivity via Equilibrium MD (Green-Kubo) using the Stillinger-Weber potential (FR-002, FR-003); (3) training a 2-layer Graph Neural Network (GNN) to predict a **Static Scattering Potential** (a topology-derived proxy) rather than dynamic heat flux, to avoid physically ill-posed mappings (FR-004); and (4) performing a **Linear Mixed-Effects Model (LMM)** analysis between the variance of these topological metrics and global thermal conductivity to quantify influence, acknowledging the limited sample size (N=2) for this proof-of-concept (FR-005, FR-006).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `torch` (CPU-only), `torch-geometric`, `ase` (Atomic Simulation Environment), `statsmodels` (for LMM), `scikit-learn`, `yaml`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `code/outputs`); no external database.  
**Testing**: `pytest` with contract tests against specific schemas: `tests/contract/test_schemas.py` validates against `contracts/thermal_sample.schema.yaml`, `contracts/atomic_graph.schema.yaml`, and `contracts/gnn_output.schema.yaml`.  
**Target Platform**: Linux (GitHub Actions free-tier: A minimal CPU configuration, ~7 GB RAM, ~ GB disk, NO GPU).  
**Project Type**: Computational research pipeline / CLI.  
**Performance Goals**: Full pipeline must complete within 6 hours on 2 CPU cores. Due to the computational cost of Green-Kubo, the sample size is reduced to **N=2** representative samples to ensure feasibility.  
**Constraints**: No GPU usage; no 8-bit/4-bit quantization; memory footprint < 7 GB.  
**Scale/Scope**: Multiple independent amorphous silicon supercells (≥atoms each); 2-layer GNN with < 1M parameters.

> **Note on Dataset Availability**: The spec assumes pre-equilibrated amorphous silicon configurations are available (N ≥ 10). The "Verified datasets" block indicates NO verified source for `ThermalSample` or `AtomicGraph`. The plan assumes these will be generated via the `code/ingest/generate_samples.py` script (using `ase` + `LAMMPS` wrapper) or fetched from a local archive if provided. If no raw data is provided, the pipeline will halt with a clear error (US-1, Edge Case: corrupted/missing input).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Mapping |
|-----------|--------|--------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/config.py`; `requirements.txt` pins all deps; `data/` checksums recorded in `state/`; `code/` runs end-to-end in isolated venv. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` restricted to verified URLs (none for `ThermalSample`/`AtomicGraph`); `Reference-Validator` will check title overlap ≥ 0.7 for any external literature cited (e.g., Stillinger-Weber potential papers). |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw/` (if provided); derivations in `data/processed/` with new filenames; checksums in `state/`; PII scan passed (no PII expected in atomic coordinates). |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to `data/processed/` rows and `code/` blocks; no hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | PASS | Artifacts carry content hashes; **Automated Update**: A post-processing hook in `code/` will update `state/projects/PROJ-366-...yaml` with `updated_at` timestamps upon any artifact change in `data/` or `code/`. |
| **VI. Numerical Stability & Simulation Fidelity** | PASS | `simulation_config.yaml` records LAMMPS version, potential file, timestep, thermostat; energy conservation checks logged; diagnostics included in provenance. |
| **VII. Model Interpretability** | PASS | LMM coefficients stored in `data/` with checksums; scripts for training, inference, and correlation executable end-to-end. |

## Project Structure

### Documentation (this feature)

```text
specs/001-topology-thermal-conductivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── thermal_sample.schema.yaml
│   ├── atomic_graph.schema.yaml
│   └── gnn_output.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-366-quantifying-the-influence-of-network-top/
├── code/
│   ├── __init__.py
│   ├── config.py               # Seeds, paths, hyperparameters
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── graph_builder.py    # FR-001: XYZ -> AtomicGraph (Å cutoff) using ase
│   │   └── sample_generator.py # Generates/loads pre-equilibrated samples (if available)
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── green_kubo.py       # FR-003: LAMMPS wrapper for Green-Kubo (SW potential)
│   │   └── config.yaml         # VI: LAMMPS version, potential, timestep, thermostat
│   ├── metrics/
│   │   ├── __init__.py
│   │   └── topology_extractor.py # FR-002: degree, clustering, shortest-path
│   ├── model/
│   │   ├── __init__.py
│   │   ├── gnn.py              # FR-004: 2-layer GNN for Static Scattering Potential
│   │   └── trainer.py          # Training loop, convergence check (SC-002)
│   └── analysis/
│       ├── __init__.py
│       └── lmm_analysis.py     # FR-005: Linear Mixed-Effects Model for correlation
├── data/
│   ├── raw/                    # Input XYZ files (if provided)
│   ├── processed/
│   │   ├── graphs/             # AtomicGraph objects (pickle/parquet)
│   │   ├── conductivities/     # Green-Kubo results
│   │   └── model_outputs/      # GNN predictions and LMM results
│   └── checksums.json          # III: Checksums for all files
├── tests/
│   ├── contract/
│   │   └── test_schemas.py     # Validates against contracts/*.schema.yaml (specific mapping)
│   ├── integration/
│   │   └── test_pipeline.py    # End-to-end on 1 sample
│   └── unit/
│       ├── test_graph_builder.py
│       └── test_metrics.py
├── requirements.txt            # Pinned dependencies
└── README.md
```

**Structure Decision**: Single-project structure (DEFAULT) chosen for simplicity and direct mapping to the research pipeline. All modules are under `code/` with clear separation of concerns (ingest, simulation, metrics, model, analysis). Tests are organized by type (unit, integration, contract).

## Complexity Tracking

> **No violations found.** The plan adheres to all constitution principles. The complexity is justified by the multi-stage nature of the research (simulation + ML + statistics), but each stage is modular and testable independently. No unnecessary layers (e.g., microservices, complex databases) are introduced.