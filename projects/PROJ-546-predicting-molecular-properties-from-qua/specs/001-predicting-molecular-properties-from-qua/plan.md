# Implementation Plan: Predicting Molecular Properties from Quantum Chemical Calculations with Limited Computational Resources

**Branch**: `001-predicting-molecular-properties` | **Date**: 2026-06-25 | **Spec**: `specs/001-predicting-molecular-properties/spec.md`
**Input**: Feature specification from `specs/001-predicting-molecular-properties/spec.md`

## Summary

This project implements a pipeline to predict molecular conformational energies using semi-empirical quantum chemical descriptors (DFTB) as a computationally efficient alternative to high-level DFT (B3LYP/def2-SVP). The core methodology involves generating electronic structure descriptors (HOMO, LUMO, Mayer bond orders) for a dataset of molecules, training Random Forest regressors on both semi-empirical and high-level subsets, and statistically comparing their predictive accuracy against DFT-calculated reference energies. The plan strictly adheres to resource constraints (CPU-only, ≤7GB RAM, ≤6h runtime) and addresses reviewer concerns regarding physical validity by explicitly modeling hydration effects where data permits and acknowledging the limitations of gas-phase calculations.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `pandas`, `rdkit`, `dftb+` (system binary), `psi4` (system binary), `requests`  
**Storage**: Local filesystem (`data/`, `code/`)  
**Testing**: `pytest` (unit tests for data parsing, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Computational chemistry research pipeline  
**Performance Goals**: Semi-empirical descriptor generation ≤ 10x faster than DFT; Model training ≤ 1 hour total.  
**Constraints**: No GPU; RAM ≤ 7GB; Disk ≤ 14GB; No external API calls during execution (datasets pre-fetched or cached); DFTB+ and Psi4 must run in CPU mode.  
**Scale/Scope**: Dataset size limited by memory; subset for DFT ≤ 30 molecules (or larger if verified dataset allows within RAM limits).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

1.  **Reproducibility (NON-NEGOTIABLE)**: Plan mandates pinned random seeds in `code/`, checksums for all data in `data/`, and a `requirements.txt` for dependency pinning.
2.  **Verified Accuracy (inherited parent Principle II)**: Plan requires citing only verified dataset URLs from the `# Verified datasets` block. External citations for methods (DFTB+, Psi4) will be validated against primary sources. Run Reference-Validator Agent on all method citations before execution.
3.  **Data Hygiene**: Raw data (Zenodo/verified sources) will be downloaded with checksums. Derived data (descriptors, model outputs) will be written to new files with derivation logs.
4.  **Single Source of Truth (inherited parent Principle I)**: All figures and statistics in the final output will be generated programmatically from the `data/` artifacts, preventing manual transcription errors.
5.  **Versioning Discipline**: All artifacts will carry content hashes; the `state` file will be updated upon successful completion of each phase.
6.  **Computational Protocol Consistency**: The plan explicitly enforces that DFTB+ and Psi4 calculations for the comparative subset use identical DFT-optimized geometries and convergence criteria to ensure valid comparison.
7.  **Resource-Bound Execution**: The plan selects CPU-tractable methods (Random Forest, small subset for DFT) and explicitly handles memory limits by streaming data or subsetting where necessary.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-molecular-properties/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-546-predicting-molecular-properties-from-qua/
├── code/
│   ├── __init__.py
│   ├── download_data.py
│   ├── generate_descriptors.py
│   ├── train_models.py
│   ├── evaluate_models.py
│   ├── sensitivity_analysis.py
│   └── requirements.txt
├── data/
│   ├── raw/             # Downloaded datasets (checksummed)
│   ├── processed/       # Descriptors, model artifacts
│   └── checksums.txt
├── tests/
│   ├── test_download.py
│   ├── test_descriptors.py
│   └── test_models.py
└── docs/
    └── reports/
```

**Structure Decision**: Single project structure chosen to minimize overhead and ensure tight integration between data generation and modeling steps, consistent with the computational chemistry workflow.

## Complexity Tracking

No complexity violations identified. The plan adheres strictly to the resource constraints and scientific rigor requirements.