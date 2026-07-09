# Implementation Plan: Investigating the Relationship Between Stellar Flare Frequency and Exoplanet Atmospheric Retention

**Branch**: `001-stellar-flare-atmospheric-retention` | **Date**: 2026-06-27 | **Spec**: `specs/001-stellar-flare-atmospheric-retention/spec.md`

## Summary

This project implements a reproducible, CPU-tractable pipeline to investigate the correlation between stellar flare frequency (via cumulative XUV flux) and exoplanet atmospheric erosion. The approach involves: (1) retrieving flare catalogs from the specific MAST 'TESS Stellar Flare Catalog' and exoplanet parameters from the NASA Exoplanet Archive; (2) filtering for M-dwarf hosts with sufficient flare history; (3) computing cumulative XUV flux and modeling mass loss via the energy-limited escape model; (4) calculating an 'Atmospheric Erosion Index' (AEI) normalized by gravitational binding energy to avoid tautological dependencies; and (5) performing a residual-based correlation analysis to isolate the flare effect from gravitational and distance baselines.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `requests`, `pandas`, `numpy`, `scipy`, `astropy`, `matplotlib`, `pyyaml`, `astroquery`  
**Storage**: Local CSV/Parquet files in `data/` (raw and derived), JSON for results, JSONL for API logs.  
**Testing**: `pytest` (unit tests for physics formulas, integration tests for data pipeline).  
**Target Platform**: GitHub Actions Free Tier (2 CPU, 7 GB RAM, 14 GB disk, no GPU).  
**Project Type**: Computational Science / Data Analysis Pipeline  
**Performance Goals**: Processing of [deferred] records in ≤ 60 seconds; memory usage < 7 GB.  
**Constraints**: No GPU; no large-LLM inference; all external API calls must handle rate limiting (exponential backoff); all derived data must be checksummed.  
**Scale/Scope**: Targeting a sample of M-dwarf systems with ≥10 recorded flares in the TESS catalog. **Note**: The provided 'Verified datasets' block does not contain the specific TESS Flare Catalog or NASA Exoplanet Archive tables; the implementation relies on the specific `astroquery` API calls identified in `research.md` to access the canonical sources directly.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Pin all dependencies in `requirements.txt`. Random seeds set in `code/`. External datasets fetched from canonical URLs (verified in research.md) with query parameters logged. |
| **II. Verified Accuracy** | **Pass** | All citations (e.g., Wright et al. 2018, energy-limited model) are validated against primary sources *during the research phase* before this plan is finalized. The `research.md` contains the verified citations. |
| **III. Data Hygiene** | **Pass** | Raw data (API responses) stored in `data/raw/` with checksums. Derived data in `data/processed/`. No in-place modification. |
| **IV. Single Source of Truth** | **Pass** | All figures and statistics in the final report will be generated directly from `data/processed/` by scripts in `code/`. |
| **V. Versioning Discipline** | **Pass** | Artifacts under `data/` and `code/` will be hashed. State file updated on changes. |
| **VI. API Data Provenance** | **Pass** | API query parameters and response timestamps logged in `data/logs/` using the schema defined in `contracts/api_log.schema.yaml`. |
| **VII. Physical Model Fidelity** | **Pass** | Use `astropy.constants` for physical constants ($G$, etc.). Explicitly document $\epsilon=0.15$, $K_{tide}=1.0$. The 'Atmospheric Erosion Index' is normalized by binding energy to ensure physical validity. |

## Project Structure

### Documentation (this feature)

```text
specs/001-stellar-flare-atmospheric-retention/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Constants, API keys, paths
├── data_ingestion.py    # FR-001, FR-008: MAST/NASA API retrieval (Specific Dataset IDs)
├── physics.py           # FR-003, FR-004, FR-005: Flux & Mass Loss models (AEI calculation)
├── analysis.py          # FR-006, FR-010: Residual-based Correlation & Sensitivity
├── visualization.py     # FR-007: Plot generation
└── utils.py             # Retry logic, checksumming, logging

tests/
├── test_physics.py      # SC-003: Synthetic unit tests (AEI validation)
├── test_data_ingestion.py
└── test_analysis.py

data/
├── raw/                 # API responses (checksummed)
├── processed/           # Derived CSVs (Flux, AEI)
└── logs/                # API query logs (JSONL)

contracts/
├── dataset.schema.yaml  # Input/Output schema validation (AEI)
├── results.schema.yaml  # Results JSON schema (Residual stats)
└── api_log.schema.yaml  # API provenance log schema
```

**Structure Decision**: Single project structure (`code/`) selected to minimize overhead for a data-science pipeline. Modular separation of `data_ingestion`, `physics`, and `analysis` ensures testability and adherence to the Single Source of Truth principle.