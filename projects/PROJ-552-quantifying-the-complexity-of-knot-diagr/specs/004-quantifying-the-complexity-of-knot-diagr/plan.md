# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-31 | **Spec**: `specs/001-knot-complexity-analysis/spec.md`
**Input**: Feature specification from `specs/001-knot-complexity-analysis/spec.md`

## Summary

Quantify knot complexity by analyzing the joint predictive relationship between crossing number and braid index for hyperbolic volume, stratified by alternating/non-alternating classification. Primary approach: download prime knot data from Knot Atlas (≤13 crossings), compute additional invariants, fit multiple regression models, and validate composite complexity scores against exploratory validation samples. Phase 1 focuses on alternating/non-alternating dichotomy with validation benchmarking at crossing number ≤10.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pandas, numpy, scikit-learn, scipy, matplotlib, seaborn, requests, pyyaml
**Storage**: File-based (CSV/Parquet under `data/`, plots under `data/plots/`, models under `models/`)
**Testing**: pytest (contract tests against schema validators)
**Target Platform**: Linux server (GitHub Actions runner)
**Project Type**: computational research library
**Performance Goals**: Dataset download within a reasonable timeframe; invariant computation within a reasonable timeframe for a small number of crossings
**Constraints**: High data completeness on required invariant fields; High algorithm validation match where reference coverage
**Scale/Scope**: The set of prime knots at crossing number 13 (per Hoste-Thistlethwaite-Weeks enumeration: ~49-50 knots); Phase 1 validation scope limited to ≤10 crossings

> Dataset size: OEIS A002863 (https://oeis.org/A002863) provides CUMULATIVE count of prime knots up to a specified crossing number threshold. The count of knots at a specific crossing number will be determined per Hoste-Thistlethwaite-Weeks enumeration. This distinction is critical for SC-001 dataset completeness validation.

## Constitution Check

**GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.**

| Principle | Status | Evidence (Plan Elements) | Notes |
|-----------|--------|--------------------------|-------|
| I. Reproducibility | ✅ PASS | `src/cli/main.py` contains `random_seed` config parameter; data downloader uses canonical URLs from verified datasets table only | Per spec.md Constitution section, random seeds pinned in code/ |
| II. Verified Accuracy | ✅ PASS | Dataset Strategy table references verified URLs: https://katlas.org (verified), https://knotinfo.math.indiana.edu (verified), https://oeis.org/A002863 (verified) | All citations verified against primary sources before inclusion |
| III. Data Hygiene | ✅ PASS | Data Model section specifies SHA-256 checksumming for all files under data/; `docs/reproducibility/` contains derivation notes with formula citations | No in-place modifications; all derivations produce new files |
| IV. Single Source of Truth | ✅ PASS | Data Flow diagram traces all figures/statistics to data rows and code blocks; RegressionOutput schema includes `created_timestamp` | No hand-typed numbers in paper; all derived from code execution |
| V. Versioning Discipline | ✅ PASS | `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml` tracks `artifact_hashes` map; content hashes update on artifact change (per spec.md Constitution section authority) | Per spec.md, every artifact carries content hash |
| VI. Mathematical Invariant Consistency | ✅ PASS | Invariant Computation Strategy references Birman-Menasco (1988), Seifert (1934), Schubert (1956) from primary mathematical literature | Computed invariants verified against established definitions |
| VII. Statistical Significance Thresholds | ✅ PASS | Statistical Analysis Plan mandates dual correlation reporting (Pearson AND Spearman) with p-values, confidence intervals, and effect sizes | All statistical claims include explicit significance thresholds |

## Project Structure

### Documentation (this feature)

```text
specs/001-knot-complexity-analysis/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── knot_record.schema.yaml
│   ├── invariants_dataset.schema.yaml
│   ├── regression_output.schema.yaml  # CANONICAL
│   ├── regression_model.schema.yaml   # LEGACY
│   └── regression_result.schema.yaml  # DEPRECATED
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
src/
├── models/
│   ├── knot_record.py
│   └── regression_model.py
├── services/
│   ├── data_downloader.py
│   ├── invariant_computer.py
│   ├── regression_fitter.py
│   └── validation_service.py
├── cli/
│   └── main.py
└── lib/
    ├── reproducibility.py
    └── statistical_tests.py

tests/
├── contract/
│   └── test_schemas.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_invariants.py
    └── test_statistical_tests.py

docs/
└── reproducibility/
    ├── invariant_algorithms.md
    ├── algorithm_validation.md
    ├── validation_scope.md
    ├── excluded_knots.md
    ├── uncomputable_invariants.md
    ├── tie_breaking_rules.md
    └── validation_status.md

data/
├── raw/
│   └── knot_atlas_export.csv
├── processed/
│   ├── invariants_dataset.parquet
│   └── exploratory_validation_sample.parquet
└── plots/
    ├── crossing_vs_braid_alternating.png
    └── crossing_vs_braid_non_alternating.png

models/                              # NEW: Model outputs directory
├── regression_models.json
└── composite_complexity_score.json

config/
└── complexity_weights.yaml
```

**Structure Decision**: Single project structure (Option 1) selected. This is a computational research library with CLI entry point, not a web service or mobile application. All code organized under `src/` with tests, documentation, and data directories at repository root.

## Complexity Tracking

No complexity violations. Single project structure sufficient for research pipeline with clear separation of concerns (data download, invariant computation, regression fitting, validation).