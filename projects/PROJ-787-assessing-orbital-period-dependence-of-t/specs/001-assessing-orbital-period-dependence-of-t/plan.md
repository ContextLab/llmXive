# Implementation Plan: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

**Branch**: `001-assessing-orbital-period-dependence` | **Date**: 2026-06-28 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-assessing-orbital-period-dependence/spec.md`

## Summary

This project implements a statistical pipeline to assess the dependence of the exoplanet radius gap on orbital period using Kepler DR25 data. The approach involves downloading and filtering the Kepler catalog, binning planets by orbital period, estimating the gap location within each bin using a two-component Gaussian Mixture Model (GMM), and validating results via Synthetic Data with known ground truth. Finally, the measured slope of the gap location vs. log(period) will be compared against theoretical predictions (photoevaporation vs. core-powered mass loss) via a z-test on a Monte Carlo generated theoretical distribution. All analysis is constrained to CPU-only execution on standard CI runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `scipy`, `astropy`, `requests`, `tqdm`, `astroquery`  
**Storage**: Local CSV/Parquet files in `data/` (raw and processed), results in `data/processed/`  
**Testing**: `pytest` (unit tests for data filtering, GMM logic, regression; integration test for full pipeline)  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest`)  
**Project Type**: Data Analysis / CLI Pipeline  
**Performance Goals**: Full pipeline execution ≤ 6 hours on 2 CPU cores, ≤ 7 GB RAM.  
**Constraints**: No GPU usage; no external APIs requiring authentication; strict data hygiene (no in-place modifications); reproducibility via pinned random seeds.  
**Scale/Scope**: [deferred] confirmed Kepler planets (after filtering); log-spaced period bins; bootstrap iterations per bin.  
**Data Sources**: Kepler DR25 Planet Table (`kplr_dr25_planet`), Kepler DR25 Validation Table (`kplr_dr25_validation`), Kepler Input Catalog (KIC).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

- **I. Reproducibility**: Plan mandates pinned random seeds in `code/` scripts and deterministic data fetching from MAST. `requirements.txt` will pin all dependencies.
- **II. Verified Accuracy**: The Reference-Validator Agent will verify the MAST archive's canonical URL and the specific product IDs (Kepler DR25 Planet Table, Kepler DR25 Validation Table `kplr_dr25_validation`) used.
- **III. Data Hygiene**: Raw data downloaded to `data/raw/` will be checksummed. Derived datasets (filtered, binned) written to `data/processed/`. No in-place edits.
- **IV. Single Source of Truth**: All figures and statistics in the final report will be generated programmatically from `data/processed/` and `code/` outputs. The canonical schema is `contracts/planet_record.schema.yaml` and `contracts/analysis_output.schema.yaml`.
- **V. Versioning Discipline**: Content hashes for all data artifacts will be recorded in `state/`. A specific step in the pipeline will update the `state/projects/...yaml` `updated_at` timestamp and artifact hashes upon any data artifact change.
- **VI. Statistical Gap Detection Rigor**: Plan explicitly implements 2-component GMM with BIC selection, minimum 1000 bootstrap resamples, and Synthetic Validation (using data with known ground truth) as required.
- **VII. Period-Binning Integrity**: Plan specifies log-spaced bins (lower-bound to 100 days), minimum 30 planets per bin (with merge logic), and weighted linear regression with z-test comparison against Monte Carlo theoretical distributions.

## Project Structure

### Documentation (this feature)

```text
specs/001-assessing-orbital-period-dependence/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── planet_record.schema.yaml   # Canonical dataset schema
│   └── analysis_output.schema.yaml # Canonical result schema
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── ingest/
│   ├── download_kepler.py
│   └── filter_data.py
├── analysis/
│   ├── binning.py
│   ├── gmm_gap_finder.py
│   ├── regression.py
│   └── theory_comparison.py
├── validation/
│   └── synthetic_validator.py
├── utils/
│   ├── logging.py
│   └── checksum.py
├── main.py
└── requirements.txt

tests/
├── unit/
│   ├── test_filter_data.py
│   ├── test_gmm_gap_finder.py
│   └── test_regression.py
├── integration/
│   └── test_full_pipeline.py
└── contract/
    └── test_schemas.py

data/
├── raw/
│   ├── kepler_dr25.csv
│   ├── kepler_dr25_validation.csv
│   └── kepler_input_catalog.csv
└── processed/
    ├── filtered_planets.csv
    ├── binned_results.csv
    └── final_analysis_results.json
```

**Structure Decision**: Selected a modular CLI pipeline structure (`code/` split by functional domain: ingest, analysis, validation). This ensures separation of concerns, facilitates unit testing of individual statistical components (GMM, regression), and aligns with the requirement for reproducibility and data hygiene. The `data/` directory is strictly read-only for raw data and append-only for processed data.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

*Note: No violations found. The proposed structure is minimal and sufficient for the scope.*

**Fallback Logic for Completeness**:
If the `kplr_dr25_validation` table is missing the `validation_efficiency` column, the pipeline will execute an **unweighted analysis**. In this mode, `completeness_weight` will be set to `1.0` for all records. The final report will explicitly flag this condition in the `validation_status` field. This ensures the pipeline remains robust even if the specific completeness metadata is unavailable, preventing a hard failure while maintaining data integrity (no imputation).