# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-12 | **Spec**: `specs/001-knot-complexity-analysis/spec.md`
**Input**: Feature specification from `specs/001-knot-complexity-analysis/spec.md`

## Summary

Download knot data from Knot Atlas for prime knots with crossing number ≤13, establish measurement precision for core invariants (crossing number, braid index), fit regression models to assess joint relationships between crossing number, braid index, and hyperbolic volume, and document all transformations for reproducibility. Phase 1 focuses on validated crossing number ≤10 data; additional invariants (arc index, Seifert circle count, bridge number) are deferred to Phase 2+.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: requests (HTTP download), pandas (data manipulation), scikit-learn (regression models), matplotlib (visualization), pyyaml (schema validation), pytest (testing)  
**Storage**: Local files (CSV/Parquet) under `data/` directory  
**Testing**: pytest with contract tests against schema definitions  
**Target Platform**: Linux server (GitHub Actions runner)  
**Project Type**: CLI/data-analysis pipeline  
**Performance Goals**: Complete analysis within 1 hour on standard compute resources  
**Constraints**: Must handle API rate limiting with exponential backoff; all data transformations must be reproducible with pinned random seeds  
**Scale/Scope**: All prime knots at crossing number ≤13 (source: OEIS A002863, https://oeis.org/A002863); total count 9988 prime knots; Phase 1 validates completeness for ≤10

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

> **Population Scope Statement**: All conclusions apply only to hyperbolic prime knots (volume > 0), not all prime knots. This selection bias is documented per FR-012.

> **Statistical Interpretation**: Regression analysis measures variance partitioning within the finite census dataset, NOT independent explanatory power. All final reports MUST explicitly state this limitation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Notes |
|-----------|------------------|---------------------|
| I. Reproducibility (NON-NEGOTIABLE) | COMPLIANT | All random seeds pinned in code; external datasets fetched from Knot Atlas on every run; `requirements.txt` at `code/` pins all dependencies |
| II. Verified Accuracy | COMPLIANT | All citations (Knot Atlas, KnotInfo, OEIS, literature) verified against primary sources before contributing review points |
| III. Data Hygiene | COMPLIANT | All files under `data/` checksummed (SHA-256); raw data preserved unchanged; transformations produce new files with documented derivation |
| IV. Single Source of Truth | COMPLIANT | All figures/statistics trace to exactly one row in `data/` and one block in `code/`; no hand-typed numbers in paper |
| V. Versioning Discipline | COMPLIANT | Every artifact carries content hash; `state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml` updated via `code/utils/checksum_utils.py` after each data transformation per FR-007 |
| VI. Mathematical Invariant Consistency | COMPLIANT | All computed invariants verified against established definitions from primary mathematical literature; discrepancies documented with derivation notes |
| VII. Statistical Significance Thresholds | COMPLIANT | All statistical claims include explicit significance thresholds and effect size measures; both Pearson and Spearman reported where distribution assumptions uncertain |

## Project Structure

### Documentation (this feature)

```text
specs/001-knot-complexity-analysis/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── knot-record.schema.yaml
│   └── regression-model.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── download/
│   ├── knot_atlas_downloader.py    # FR-001, FR-008 (download with retry logic)
│   └── retry_utils.py              # Exponential backoff implementation
├── data/
│   ├── validator.py                # FR-002, FR-009 (data quality validation only)
│   ├── parser.py                   # FR-002 (parsing and cleaning)
│   ├── filter_hyperbolic.py        # FR-012 (hyperbolic filtering - SEPARATE from validator.py)
│   └── reproducibility/
│       ├── data_quality_report.md  # FR-002 output
│       ├── validation_scope.md     # SC-001 output (≤10 vs ≤13 distinction)
│       ├── excluded_knots.md       # FR-012 output (torus/satellite exclusions)
│       ├── invariant_coverage.md   # SC-008 output (core invariant availability)
│       ├── algorithm_validation.md # SC-010 output (Phase 2+ only for additional invariants)
│       ├── hyperbolic_volume_validation.md  # FR-013 output
│       ├── multicollinearity_assessment.md  # FR-005 output
│       ├── residual_analysis.md    # SC-011 output
│       ├── tie_breaking_rules.md   # SC-007 output
│       ├── random_seeds.md         # FR-007 output
│       └── validation_status.md    # SC-007 output
├── analysis/
│   ├── exploratory.py              # FR-004 (EDA, scatter plots)
│   ├── regression.py               # FR-005 (model fitting)
│   └── statistics.py               # FR-006 (correlation tests, effect sizes)
├── utils/
│   ├── checksum_utils.py           # FR-007 (SHA-256 checksumming, state file updates)
│   └── logging_utils.py            # FR-007 (timestamped logs)
└── tests/
    ├── contract/
    │   ├── test_knot_record_schema.py
    │   └── test_regression_model_schema.py
    ├── integration/
    │   └── test_download_pipeline.py
    └── unit/
        ├── test_retry_logic.py     # SC-004
        └── test_tie_breaking.py    # SC-007 validation script

data/
├── raw/
│   └── knot_atlas_export.csv       # Raw download (checksummed)
├── processed/
│   ├── knots_cleaned.parquet       # FR-002 cleaned dataset (checksummed)
│   ├── knots_hyperbolic.parquet    # FR-012 filtered dataset (checksummed)
│   └── invariants_summary.parquet  # Derived dataset (checksummed)
└── plots/
    ├── crossing_vs_braid_alternating.png  # FR-004 output
    └── crossing_vs_braid_nonalternating.png  # FR-004 output

docs/
├── reproducibility/
│   ├── derivation_notes.md         # FR-007 (transformation logic)
│   ├── invariant_algorithms.md     # FR-003 (Phase 2+ algorithms)
│   └── uncomputable_invariants.md  # FR-003 (Phase 2+ uncomputable records)
└── paper/
    └── draft.md                    # Final manuscript
```

**Structure Decision**: Single-project structure with clear separation between download, data processing, analysis, and utility modules. This aligns with Constitution Principle I (Reproducibility) by ensuring all code is runnable end-to-end without manual intervention. The `data/reproducibility/` directory under `code/` is used for validation scripts and logs per FR-007 requirements.

**File Independence**: `code/data/validator.py` (data quality validation) and `code/data/filter_hyperbolic.py` (hyperbolic filtering) are now separate files to prevent parallel execution conflicts. No [P] parallel tags remain on tasks modifying these files.

## Complexity Tracking

> **No violations requiring justification** - All complexity is necessary to meet functional requirements and constitution principles.

## Resolved Concerns from Previous Iteration

**Concern T009, T010, T043a (parallel file conflicts)**: These tasks have been split into separate files:
- `code/data/validator.py` handles data quality validation (FR-002, FR-009)
- `code/data/parser.py` handles parsing and cleaning (FR-002)
- `code/data/filter_hyperbolic.py` handles hyperbolic filtering (FR-012) - NEW SEPARATE FILE
- `code/download/knot_atlas_downloader.py` handles download operations (FR-001, FR-008)

Each file is now independent with no shared state, allowing parallel-safe execution where applicable. **No [P] tags remain on any tasks.**

**Concern T026 (algorithm_validation.md semantic boundary)**: The `docs/reproducibility/algorithm_validation.md` document is now explicitly reserved for Phase 2+ additional invariants only (arc index, Seifert circle count, bridge number). Core invariants (crossing number, braid index) are TABULATED from Knot Atlas per SC-008 and FR-003, not computed. Algorithm validation does not apply to tabulated data. This separation is documented in the task definitions and enforced through the validation workflow.

**Concern plan_consistency-a5c9971f (checksum field naming)**: Standardized field name to 'checksum' throughout data-model.md and all contract schemas. Removed 'checksum_sha256' variant.

**Concern methodology-b4bd3e6f, methodology-1b302f62 (explanatory power language)**: Revised all references from 'explanatory power' to 'describe joint relationships' to accurately reflect census data statistical interpretation.

**Concern scientific_soundness-e80dd3b0 (source independence)**: FR-013 now explicitly documents that Knot Atlas and KnotInfo may share Hoste-Thistlethwaite-Weeks enumeration, making validation a consistency cross-check NOT independent verification.

**Concern methodology-f1cff0d7 (OEIS citation for prime knot count)**: Updated Technical Context to explicitly cite OEIS A002863 as the source for the 9988 prime knots count at crossing number ≤13, enabling verification.

**Concern data_resources-0b62766d (KnotInfo URL in FR-013)**: The research.md document includes the KnotInfo endpoint URL (https://knotinfo.math.indiana.edu/knotinfo/) in its Source Independence Documentation section. However, the source spec (spec.md) FR-013 requires a separate update to include this URL for self-contained reproducibility per Constitution Principle I. This is flagged for spec-root cause resolution.