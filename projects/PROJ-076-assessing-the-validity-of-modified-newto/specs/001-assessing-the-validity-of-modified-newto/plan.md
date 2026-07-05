# Implementation Plan: Assessing the Validity of Modified Newtonian Dynamics with Galaxy Rotation Curves

**Branch**: `[001-assess-mond-validity]` | **Date**: 2026-06-24 | **Spec**: `specs/001-assessing-mond-validity/spec.md`
**Input**: Feature specification from `/specs/001-assessing-mond-validity/spec.md`

## Summary

This project implements a rigorous statistical comparison between Modified Newtonian Dynamics (MOND) and the standard NFW dark matter halo model using galaxy rotation curve data from the SPARC database. The pipeline downloads raw data, filters for quality (inclination uncertainty <10°, ≥15 points), fits both models with velocity uncertainty weighting (MOND with a free parameter: M/L; NFW with free parameters: c, rs), computes goodness-of-fit metrics (reduced χ², AIC, BIC, Kolmogorov-Smirnov test), performs parametric bootstrap residual analysis with Holm-Bonferroni correction, and conducts sensitivity analysis on χ² thresholds. All findings are framed as associational due to the observational nature of the data.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `scipy`, `numpy`, `pandas`, `requests`, `pyyaml`, `pytest`  
**Storage**: Local filesystem (`data/`, `results/`) with checksummed artifacts  
**Testing**: `pytest` with contract validation against `contracts/dataset.schema.yaml` and `contracts/fit_results.schema.yaml`  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, ~7 GB RAM, ~ GB disk)  
**Project Type**: Computational research pipeline / CLI  
**Performance Goals**: <6 hours total runtime; <30s per galaxy fit; <7 GB peak RAM  
**Constraints**: No GPU/CUDA; no large-LLM inference; CPU-only `scipy.optimize`; memory-optimized data loading (chunking if necessary); deterministic random seeds  
**Scale/Scope**: ~ galaxies (SPARC full sample); A large number of radial points total; threshold sweeps  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Check | Status |
|-----------|------------------|--------|
| I. Reproducibility | Random seeds pinned in `code/`; SPARC fetched from canonical source; `requirements.txt` pins versions | ✅ |
| II. Verified Accuracy | All citations (Milgrom 1983, NFW, SPARC) validated against primary sources; title overlap ≥0.7 enforced by validator | ✅ |
| III. Data Hygiene | Raw SPARC files checksummed; filtering scripts in `code/`; no in-place edits; `data/metadata.yaml` records version/date | ✅ |
| IV. Single Source of Truth | All figures/stats trace to `data/` rows and `code/` blocks; no hand-typed numbers in paper | ✅ |
| V. Versioning Discipline | Content hashes tracked in `state/...yaml`; artifact changes update `updated_at` | ✅ |
| VI. Observational Data Integrity | SPARC data obtained directly; download date/version logged; filtering via scripts; no manual edits | ✅ |
| VII. Model Comparison Transparency | MOND/NFW modules in `code/models/`; `curve_fit` with priors; `results/fit_summary.csv` standardized output including Kolmogorov-Smirnov test results | ✅ |

## Project Structure

### Documentation (this feature)

```text
specs/001-assessing-mond-validity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── fit_results.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-076-assessing-the-validity-of-modified-newto/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── download.py
│   ├── preprocess.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── mond.py
│   │   └── nfw.py
│   ├── fit.py
│   ├── metrics.py
│   ├── residuals.py
│   └── sensitivity.py
├── data/
│   ├── raw/
│   │   └── sparc/
│   ├── processed/
│   │   └── filtered_galaxies.csv
│   └── metadata.yaml
├── results/
│   ├── fit_summary.csv
│   ├── residual_stats.csv
│   └── sensitivity_report.csv
├── tests/
│   ├── contract/
│   │   └── test_schemas.py
│   ├── unit/
│   │   ├── test_mond.py
│   │   └── test_nfw.py
│   └── integration/
│       └── test_pipeline.py
└── state/
    └── projects/PROJ-076-assessing-the-validity-of-modified-newto.yaml
```

**Structure Decision**: Single-project structure chosen for computational research pipeline. All code under `code/`, data under `data/`, results under `results/`. This ensures reproducibility, clear separation of concerns, and compatibility with GitHub Actions free-tier constraints.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | No violations detected; all complexity justified by scientific requirements (dual-model fitting, parametric bootstrap, sensitivity sweeps, KS tests) | Direct comparison without bootstrap or sensitivity would violate FR-009, FR-010, FR-012 and undermine statistical rigor; permutation test rejected due to exchangeability violations |