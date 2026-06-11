# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-31 | **Spec**: specs/004-quantifying-the-complexity-of-knot-diagr/spec.md
**Input**: Feature specification from specs/004-quantifying-the-complexity-of-knot-diagr/spec.md

## Summary

This feature implements a computational research pipeline to quantify knot diagram complexity through the joint analysis of crossing number and braid index as predictors of hyperbolic volume. The technical approach involves: (1) downloading prime knot data from Knot Atlas for crossing numbers ≤13, (2) computing additional invariants (arc index, Seifert circle count, bridge number) from diagram representations, (3) performing exploratory data analysis with stratified visualization, (4) fitting multiple regression models (linear, polynomial, logarithmic), and (5) validating a composite complexity score against an exploratory correlation sample. Phase 1 scope is explicitly limited to alternating/non-alternating dichotomy and validated crossing number ≤10 data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas==2.1.4, numpy==1.26.3, scikit-learn==1.4.0, scipy==1.12.0, matplotlib==3.8.2, pyyaml==6.0.1, requests==2.31.0, tqdm==4.66.1, datasets==2.16.1  
**Storage**: File-based (CSV/Parquet) under data/ directory  
**Testing**: pytest==7.4.3 with contract tests against schema validation  
**Target Platform**: Linux server (GitHub Actions runner)  
**Project Type**: computational research pipeline  
**Performance Goals**: Dataset download within a reasonable timeframe for ≤13 crossing numbers; invariant computation within reasonable time for all knots; regression fitting within a short timeframe  
**Constraints**: Retry logic with exponential backoff (initial delay, multiplier, maximum duration); partial results cached after 3 consecutive failures; checksums (SHA-256) for all data files  
**Scale/Scope**: A known quantity of prime knots total (OEIS sequence); Phase 1 validation benchmarked on ≤10 crossing numbers

> Dataset completeness for crossing numbers 11-13 is downloaded but not validated in Phase 1. This is a deliberate scope decision per SC-001, documented in docs/reproducibility/validation_scope.md.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Implementation Strategy | Status |
|-----------|-------------|------------------------|--------|
| I. Reproducibility | Random seeds pinned; external datasets from canonical source | A fixed random seed pinned in code/ via config/seeds.yaml; Knot Atlas download via requests with deterministic retry logic | ✅ PASS |
| II. Verified Accuracy | Citations verified against primary source | Reference-Validator Agent runs at artifact write; citation title overlap ≥ high threshold | ✅ PASS |
| III. Data Hygiene | Checksums recorded; no in-place modification | SHA-256 checksums in data/checksums.txt; all transformations produce new files under data/derived/ | ✅ PASS |
| IV. Single Source of Truth | All figures/statistics trace to data/ and code/ | Jupyter notebooks under code/ analysis/; all derived numbers computed from data files, not hand-typed | ✅ PASS |
| V. Versioning Discipline | Content hash for every artifact; state file updated | Each artifact carries content hash; state file PROJ-552 updated on artifact change | ✅ PASS |
| VI. Mathematical Invariant Consistency | Computed invariants verified against established definitions | Algorithm validation against KnotInfo reference values where coverage permits; documented in docs/reproducibility/algorithm_validation.md | ✅ PASS |
| VII. Statistical Significance Thresholds | All claims include p-values, confidence intervals, effect sizes; both Pearson AND Spearman reported; descriptive framing for finite census | Correlation analyses report both coefficients; ANOVA includes Levene's/Shapiro-Wilk assumption checks; effect sizes (Cohen's d, r) documented; p-values reported with explicit 'exploratory/discovery' disclaimer | ✅ PASS |

**Constitution Check Summary**: All principles satisfied. No violations requiring complexity justification.

## Project Structure

### Documentation (this feature)

```text
specs/004-quantifying-the-complexity-of-knot-diagr/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── knot_record.schema.yaml    # Contract for KnotRecord entity
│   ├── regression_output.schema.yaml  # Contract for RegressionModel entity
│   └── composite_score_output.schema.yaml  # Contract for CompositeComplexityScore entity
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── downloader/
│   ├── __init__.py
│   ├── knot_atlas_client.py      # FR-001, FR-010
│   └── retry_logic.py            # FR-010
├── invariant_computation/
│   ├── __init__.py
│   ├── arc_index.py              # FR-003 (Birman-Menasco)
│   ├── seifert_circles.py        # FR-003 (Seifert's algorithm)
│   └── bridge_number.py          # FR-003 (Schubert's decomposition)
├── analysis/
│   ├── __init__.py
│   ├── exploratory_analysis.py   # FR-004, FR-005
│   ├── regression_models.py      # FR-005
│   └── composite_score.py        # FR-006, FR-007
├── reproducibility/
│   ├── __init__.py
│   ├── logs.py                   # FR-009
│   └── validation.py             # SC-008, SC-012
├── main.py                       # Orchestration entry point
└── config/
    ├── seeds.yaml                # Random seed pinning (FR-009)
    ├── complexity_weights.yaml   # FR-006 (supports sensitivity analysis)
    └── requirements.txt          # Dependency pinning

data/
├── raw/
│   └── knot_atlas_export.csv     # Downloaded data (checksummed)
├── derived/
│   ├── invariants_computed.csv   # FR-002, FR-003
│   ├── regression_results.csv    # FR-005
│   └── composite_score_results.csv  # FR-006
├── plots/
│   ├── crossing_vs_braid_alternating.png  # FR-004
│   └── crossing_vs_braid_non_alternating.png  # FR-004
└── checksums.txt                 # SHA-256 checksums (Constitution III)

docs/
└── reproducibility/
    ├── validation_scope.md       # SC-001, SC-013
    ├── algorithm_validation.md   # FR-003, SC-012
    ├── tie_breaking_rules.md     # SC-008
    ├── excluded_knots.md         # FR-014
    ├── uncomputable_invariants.md  # FR-003
    ├── validation_status.md      # SC-008
    └── selection_bias.md         # FR-014 (hyperbolic knot limitation)

tests/
├── contract/
│   ├── test_knot_record.py       # Validates against knot_record.schema.yaml
│   ├── test_regression_output.py # Validates against regression_output.schema.yaml
│   └── test_composite_score.py   # Validates against composite_score_output.schema.yaml
├── integration/
│   └── test_pipeline.py
└── unit/
    └── test_invariants.py
```

**Structure Decision**: Single computational project structure selected. The code/ directory contains all Python modules organized by functional responsibility (downloader, invariant_computation, analysis, reproducibility). This structure aligns with Constitution Principle I (reproducibility) by enabling isolated virtualenv execution and Constitution Principle IV (single source of truth) by keeping all data transformations in code/ with outputs in data/.

**Contract Test Traceability**: All entities in data-model.md have corresponding contract schemas in contracts/. Contract tests in tests/contract/ validate that code outputs match schema definitions. This ensures data integrity throughout the pipeline.

**Entity Reference**: The InvariantsDataset entity (data-model.md) represents the aggregated collection of KnotRecord entities and is instantiated in code/analysis/exploratory_analysis.py. All derived CSV files correspond to this entity structure.

## Complexity Tracking

> Constitution Check has no violations; complexity tracking table omitted.