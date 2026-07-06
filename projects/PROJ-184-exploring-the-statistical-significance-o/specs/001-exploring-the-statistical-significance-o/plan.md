# Implementation Plan: Exploring the Statistical Significance of Fine‑Structure Constant Variations

**Branch**: `001-fine-structure-constant-variations` | **Date**: 2026-06-27 | **Spec**: [link]
**Input**: Feature specification from `specs/001-fine-structure-constant-variations/spec.md`

## Summary

This project implements a reproducible, hierarchical Bayesian analysis pipeline to estimate the fractional variation in the fine-structure constant (Δα/α) using **verified, real-world quasar absorption-line spectra** from the ESO UVES Large Programme 094.C-0462. The approach adheres to the project constitution's requirements for reproducibility, data hygiene, and rigorous statistical modeling (PyMC, NUTS sampling). The pipeline ingests UVES spectra, extracts metal absorption lines (Fe II, Mg II, Si IV, C IV, Al III), models systematic errors as nuisance parameters with physically realistic priors, and performs model comparison (Null vs. Temporal vs. Dipole) using Bayes Factors. All analysis is constrained to run on free-tier GitHub Actions CPU resources (≤6h, ≤7GB RAM).

*Note: Simulation is used **only** for code validation (SC-001, SC-002) to verify that the pipeline can recover injected parameters. All production scientific results (FR-005, US-3) are derived exclusively from the real ESO dataset.*

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymc>=5.0.0`, `arviz>=0.15.0`, `astropy>=5.3.0`, `specutils>=1.10.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `requests>=2.31.0`, `scipy>=1.11.0`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `data/interim/`) with checksums recorded in `state/`  
**Testing**: `pytest` with `pytest-cov` for unit/integration tests; simulated data generators for validation  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM, no GPU)  
**Project Type**: Scientific CLI / Analysis Pipeline  
**Performance Goals**: Full analysis (20 simulated absorbers, 4 chains, 2000 warmup, 4000 draws) must complete in ≤4 hours with ≤5 GB RAM  
**Constraints**: No GPU usage; no large-LLM inference; data subsets to fit RAM; all random seeds pinned; no hardcoded fabricated metrics  
**Scale/Scope**: ~30 absorbers (production from ESO), 20 absorbers (benchmark simulation); ~1000 absorption lines total

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|----------------------|
| **I. Reproducibility** | ✅ Compliant | Random seeds pinned in `code/`; all external datasets fetched from canonical sources (ESO LP 094.C-0462, NIST, SDSS DR16); `requirements.txt` pins versions; isolated venv per run. |
| **II. Verified Accuracy** | ✅ Compliant | All citations (NIST, ESO, SDSS) verified via Reference-Validator; verified URLs present in `research.md`; title overlap ≥0.7 enforced; no fabricated URLs. |
| **III. Data Hygiene** | ✅ Compliant | Raw data checksummed in `state/`; no in-place modifications; derivations produce new files; PII scan enforced. |
| **IV. Single Source of Truth** | ✅ Compliant | All figures/tables generated from `data/` and `code/`; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | ✅ Compliant | Content hashes for all artifacts; `updated_at` timestamps updated on change. |
| **VI. Hierarchical Bayesian Modeling** | ✅ Compliant | Two-level structure (Level 1: per-absorber Δα/α; Level 2: global trend/dipole) implemented in PyMC v5 with NUTS; 4 chains, 2000 warmup, 4000 draws. |
| **VII. Systematic-Error Documentation** | ✅ Compliant | Systematics (calibration drift, intra-order distortion) encoded as nuisance parameters with informative priors (Half-Cauchy scale=0.001 Å if calibration data unavailable). |

**GATE RESULT**: PASS. All constitutional principles are addressed in the plan. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-fine-structure-constant-variations/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Static Schema Definitions)
│   ├── absorber.schema.yaml
│   ├── delta_alpha_schema.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py              # Paths, seeds, hyperparameters
├── data/
│   ├── download_esodata.py   # FR-001: ESO UVES ingestion
│   ├── extract_lines.py      # FR-002: Line extraction with specutils
│   └── preprocess.py         # FR-004: Systematic error derivation
├── models/
│   ├── hierarchical.py       # FR-003: PyMC hierarchical model
│   ├── dipole.py             # FR-006: Spatial dipole model
│   └── comparison.py         # FR-005: Bayes factor computation
├── analysis/
│   ├── run_analysis.py       # Main orchestration script
│   ├── sensitivity.py        # FR-005/007: Sensitivity & convergence checks
│   └── visualize.py          # FR-008: Corner plots, summary tables
├── tests/
│   ├── unit/
│   │   ├── test_download.py
│   │   └── test_extract.py
│   ├── integration/
│   │   └── test_hierarchical_model.py  # Simulated data coverage test
│   └── contract/
│       └── test_schemas.py
├── requirements.txt
└── README.md

data/
├── raw/                    # Downloaded FITS files (checksummed)
├── processed/              # Extracted line lists (CSV)
├── interim/                # Preprocessed absorber data
└── results/                # Posterior samples, Bayes factors, plots

state/
└── projects/PROJ-184-.../
    └── artifact_hashes.yaml
```

**Structure Decision**: Single `code/` directory with modular subpackages (`data`, `models`, `analysis`, `tests`) to enforce separation of concerns, ensure testability, and support the hierarchical modeling standard (Constitution Principle VI). All data flows through `data/` with checksums in `state/`. The `contracts/` directory contains static schema definitions used for validation, not generated artifacts, ensuring alignment with the 'Single Source of Truth' principle.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations detected. Complexity is justified by the scientific requirements (hierarchical Bayesian inference, systematic error modeling, model comparison) and constitutional mandates. Simpler alternatives (e.g., fixed-effects models, no systematics) would violate Principle VI and VII.*