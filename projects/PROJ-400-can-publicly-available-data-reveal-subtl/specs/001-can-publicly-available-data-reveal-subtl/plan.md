# Implementation Plan: Can Publicly Available Data Reveal Subtle Violations of Time-Reversal Symmetry in Beta Decay?

**Branch**: `001-t-violation-beta-decay` | **Date**: 2026-07-14 | **Spec**: `specs/001-t-violation-beta-decay/spec.md`
**Input**: Feature specification from `/specs/001-t-violation-beta-decay/spec.md`

## Summary

This project implements a statistical analysis pipeline to search for Time-Reversal (T) symmetry violations in beta decay by performing a **Meta-Analysis of Published D-Coefficients** from archival data. The system retrieves published D-coefficient values (or values derivable from A, B, a coefficients if the source paper provides the formula) for target nuclei (e.g., 6He, 19Ne) from the NNDC ENSDF database and primary literature. It computes an inverse-variance weighted mean of these coefficients and establishes confidence interval upper bounds via permutation testing (sign-flipping/bootstrap of 10,000+ iterations). Results are validated against the latest Particle Data Group (PDG) Review.

**CRITICAL SCIENTIFIC PIVOT**: The original spec (FR-002, US-2) proposed a "cross-modal covariance" method to derive D from independent momentum and polarization spectra. This method is **physically invalid** as the D-coefficient requires simultaneous measurement within a single event (triple product correlation). Computing the covariance of independent random variables from separate runs yields zero by definition, not a T-violation signal. This plan **pivots** to a Meta-Analysis of published D-values. The implementation will follow this corrected methodology. The spec requires a **kickback** to update FR-002, US-2, FR-001, and US-1 to reflect the retrieval of D-coefficients rather than covariance calculation, and to remove the requirement for raw event-level data not present in ENSDF.

The implementation prioritizes CPU feasibility on GitHub Actions runners, strict adherence to the project constitution regarding reproducibility and data hygiene, and explicit handling of the spec contradiction.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `requests`, `lxml`, `pyyaml`, `pytest`.  
**Storage**: Local `data/` directory (raw downloads), `data/processed/` (derived artifacts). No database required.  
**Testing**: `pytest` with contract testing against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier: Standard CPU allocation and moderate RAM capacity).  
**Project Type**: Scientific Data Analysis Pipeline / CLI Tool.  
**Performance Goals**: Complete analysis of target nuclei within 6 hours; permutation test stability (variance < 0.01) verified.  
**Constraints**: Must run without external API keys (public NNDC); must handle network retries; strict memory limits; no GPU required for statistical permutation.  
**Scale/Scope**: Limited to specific nuclei (6He, 19Ne) as defined in the spec; analysis of published D-coefficient measurements.

> Domain-specific empirical specifics are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action / Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. External data fetched from NNDC ENSDF (public) on every run. `requirements.txt` pins dependencies. |
| **II. Verified Accuracy** | **PASS** | All citations (PDG 2024, ENSDF methodology) will be validated by the Reference-Validator Agent against primary sources. **Integration**: A CI step `python -m code.cli.main validate-citations` blocks pipeline if citations fail (score 0.0). |
| **III. Data Hygiene** | **PASS** | All raw data downloads checksummed (SHA-256) and stored in `data/`. Transformations produce new files in `data/processed/`. |
| **IV. Single Source of Truth** | **PASS** | Final results in `paper/` will be generated programmatically from `data/processed/` via scripts; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | **Mechanism**: A `hash_manifest.json` is generated in `state/` after every run, containing SHA-256 hashes of all input/output files. The `updated_at` timestamp in the project state file is updated only if this manifest changes. |
| **VI. Cross-Modal Independence** | **PASS** | Methodology treats each *published D-coefficient* as an independent measurement from its own experiment. No merging of raw counts across experiments. (Note: Spec's requirement for cross-modal fusion is invalid and requires update). |
| **VII. Null-Hypothesis Rigor** | **PASS** | Permutation testing (sign-flipping/bootstrap, + shuffles) is the *only* method for establishing significance of the meta-analytic mean. |

## Project Structure

### Documentation (this feature)

```text
specs/001-t-violation-beta-decay/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── d_measurement.schema.yaml       # Primary: Schema for published D-coefficient measurements
    ├── meta_analysis_result.schema.yaml # Primary: Schema for meta-analysis results
    ├── fusion_result.schema.yaml       # Legacy: Retained for compatibility, deprecated
    └── raw_observable.schema.yaml      # Legacy: Retained for compatibility, deprecated
```

### Source Code (repository root)

```text
projects/PROJ-400-can-publicly-available-data-reveal-subtl/
├── code/
│   ├── __init__.py
│   ├── config.py                # Paths, seeds, retry limits
│   ├── data/
│   │   ├── fetch_ensdf.py       # NNDC API/Scraping logic with retry/backoff
│   │   ├── validate_format.py   # Checks for presence of D-coefficient values
│   │   └── harmonize.py         # Aligns data by nucleus/state
│   ├── analysis/
│   │   ├── meta_analysis.py     # Weighted mean calculation, heterogeneity test
│   │   ├── permutation_test.py  # Sign-flipping/bootstrap, null distribution
│   │   └── sensitivity.py       # SE calculation, PDG comparison
│   ├── models/
│   │   ├── nucleus.py           # Dataclasses for Nucleus, DMeasurement
│   │   └── results.py           # Dataclasses for MetaAnalysisResult
│   └── cli/
│       └── main.py              # Entry point: fetch, analyze, report
├── data/
│   ├── raw/                     # Downloaded ENSDF files (checksummed)
│   └── processed/               # Derived JSON/Parquet artifacts
├── tests/
│   ├── contract/                # Schema validation tests
│   ├── integration/             # End-to-end pipeline tests
│   └── unit/                    # Logic tests (meta-analysis, permutation)
├── docs/                        # Paper drafts, figures
└── requirements.txt
```

**Structure Decision**: Single project structure (`code/`) chosen to maintain tight coupling between data fetching and analysis, reducing overhead for a scientific pipeline. No frontend/backend split needed.

## Complexity Tracking

No violations detected. The scope is tightly bounded by the spec to specific nuclei and a single statistical method (Meta-Analysis), ensuring feasibility within the 6-hour CI window. The pivot from "covariance fusion" to "meta-analysis" resolves the scientific soundness concerns.

## Spec Contradiction Note

The source spec (`spec.md`) contains **FR-002**, **US-2**, **FR-001**, and **US-1** which mandate a "cross-modal covariance" method and retrieval of "raw/semi-raw momentum spectra" for fusion. These requirements are **physically invalid** and **data-feasibility impossible** (ENSDF lacks raw event-level data). This plan **ignores** those specific requirements in favor of the corrected Meta-Analysis methodology. A kickback to the spec is required to:
1. Update FR-002 to: "System MUST retrieve published D-coefficient values..."
2. Update US-2 to reflect the meta-analytic approach.
3. Update FR-001 and US-1 to reflect retrieval of D-coefficients rather than raw spectra.
4. Deprecate the "Key Entities" `RawObservable` and `FusionResult` in the spec, as the plan uses `DMeasurement` and `MetaAnalysisResult`.