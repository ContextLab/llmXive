# Implementation Plan: Testing the Equivalence Principle with Satellite Laser Ranging

**Branch**: `001-testing-equivalence-principle` | **Date**: 2026-06-21 | **Spec**: `specs/001-testing-equivalence-principle/spec.md`

## Summary

This feature implements a computational pipeline to test the Weak Equivalence Principle (WEP) by analyzing Satellite Laser Ranging (SLR) data for geodetic satellites (LAGEOS-1, LAGEOS-2, Etalon-1, Etalon-2, Starlette). The approach involves downloading normal-point series, performing a **joint weighted least-squares orbit determination** to estimate a shared composition-dependent parameter ($\\eta$), and conducting robustness checks via geopotential model sensitivity analysis and multiple-comparison corrections. The entire pipeline is constrained to run on a CPU-only, time-limited GitHub Actions free-tier runner.

**Critical Methodology Update**: Unlike the initial draft, this plan does *not* estimate non-gravitational accelerations separately and subtract them. Instead, it employs a **differential observable** strategy within a **joint estimation framework**. This ensures common-mode errors (e.g., geopotential) cancel out, isolating the differential gravitational signal ($a_c$) required to test WEP.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `requests`, `pyyaml`, `astropy` (for coordinate/time handling), `pyproj` (for geodetic calculations)  
**Storage**: Local CSV/Parquet files in `data/` (raw), `data/processed/` (cleaned), `data/results/` (outputs). No external database.  
**Testing**: `pytest` with `pytest-cov`.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Scientific data analysis CLI / pipeline.  
**Performance Goals**: Complete full pipeline (ingestion + estimation + validation) within 6 hours on 2 vCPU, 7GB RAM.  
**Constraints**: No GPU usage; no large-LLM inference; memory footprint < 6GB; strict adherence to verified dataset URLs.  
**Scale/Scope**: Multi-year SLR data for satellites; geopotential models; A substantial number of normal points per satellite.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| **I. Reproducibility** | **COMPLIANT** | Plan mandates pinned random seeds, isolated `requirements.txt`, and re-runnable scripts. |
| **II. Verified Accuracy** | **BLOCKING** | **NO verified source** exists in the `# Verified datasets` block for LAGEOS/Etalon SLR data. The plan **cannot proceed** until a verified URL is added. The implementation will raise a `DataUnavailableError` if this block is empty. |
| **III. Data Hygiene** | **COMPLIANT** | Plan requires checksumming raw data, immutable derivations, and no PII (irrelevant for satellite telemetry). |
| **IV. Single Source of Truth** | **COMPLIANT** | Output schemas and code will ensure all statistics trace to specific data rows. |
| **V. Versioning Discipline** | **COMPLIANT** | Artifacts will carry content hashes; state files updated on change. |
| **VI. Instrument Calibration** | **COMPLIANT** | Plan explicitly sources data from ILRS (via verified proxies) and documents preprocessing scripts. |
| **VII. Statistical Rigor** | **COMPLIANT** | Plan mandates confidence intervals, covariance propagation, and multiple-comparison corrections. |

## Project Structure

### Documentation (this feature)

```text
specs/001-testing-equivalence-principle/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── normal_point.schema.yaml
│   ├── orbit_solution.schema.yaml
│   └── eotvos_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Entry point for pipeline orchestration
├── config.py            # Configuration loading (paths, hyperparams, benchmarks)
├── data/
│   ├── __init__.py
│   ├── ingestion.py     # FR-001: Download and parse SLR normal points (HALTS if no verified source)
│   └── preprocessing.py # FR-001: Quality filtering, time alignment
├── models/
│   ├── __init__.py
│   ├── dynamics.py      # FR-002: Geopotential, drag, SRP, relativity models
│   └── estimator.py     # FR-003: Joint weighted least-squares solver (estimates $\\eta$ directly)
├── analysis/
│   ├── __init__.py
│   ├── eotvos.py        # FR-004: Calculate $\\eta$ and confidence intervals from joint fit
│   ├── validation.py    # FR-005, FR-006: Sensitivity analysis, Likelihood Ratio Test, corrections
│   └── report.py        # FR-007: Diagnostic report generation
├── utils/
│   ├── __init__.py
│   └── logging.py       # Standardized logging and error handling
├── tests/
│   ├── __init__.py
│   ├── test_ingestion.py
│   ├── test_estimator.py
│   └── test_validation.py
└── requirements.txt     # Pinned dependencies

contracts/
├── normal_point.schema.yaml
├── orbit_solution.schema.yaml
└── eotvos_result.schema.yaml

data/
├── raw/                 # Downloaded SLR normal points (checksummed)
├── processed/           # Cleaned, aligned datasets
└── results/             # Orbit solutions, $\\eta$ estimates, plots
```

**Structure Decision**: Single-project structure chosen to minimize overhead for a scientific pipeline. All logic is modularized by domain (data, models, analysis) to ensure testability and maintainability. No frontend/backend split required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Joint Estimation** | Required to cancel common-mode geopotential errors and isolate the differential WEP signal. | Independent fits were rejected because they conflate WEP violations with modeling errors (see Methodology). |

