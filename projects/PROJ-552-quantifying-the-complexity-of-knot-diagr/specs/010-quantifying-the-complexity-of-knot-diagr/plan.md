# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-12 | **Spec**: `specs/010-quantifying-the-complexity-of-knot-diagr/spec.md`
**Input**: Feature specification from `/specs/010-quantifying-the-complexity-of-knot-diagr/spec.md`

## Summary

This feature implements a computational pipeline to download, parse, and analyze prime knot data from Knot Atlas, focusing on crossing number and braid index as core invariants. The analysis establishes measurement precision thresholds, fits multiple regression models to assess joint predictive relationships with hyperbolic volume, and documents all transformations for reproducibility. Phase 1 is explicitly limited to core invariants and validated crossing number ≤10 data, with additional invariants and full validation at crossing numbers 11-13 deferred to Phase 2+.

**Census Data Scope**: Analysis covers all prime knots with crossing number up to a defined threshold (per OEIS A002863). Phase 1 validation limited to crossing number ≤10. Hyperbolic volume filtering (volume > 0) restricts analysis to hyperbolic prime knots only; conclusions about non-hyperbolic prime knots (torus/satellite) are explicitly NOT possible.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, matplotlib, seaborn, scikit-learn, requests, pyyaml, datasets  
**Storage**: Local files (CSV/Parquet), no external database  
**Testing**: pytest with contract tests for schema validation  
**Target Platform**: Linux (GitHub Actions compatible)  
**Project Type**: computational-research-pipeline  
**Performance Goals**: Complete pipeline execution within standard CI job budget  
**Constraints**: Data download retry logic with exponential backoff; reproducibility via pinned random seeds and checksums  
**Scale/Scope**: Prime knots up to a moderate crossing number (approximately ten thousand total per OEIS A002863), with Phase 1 validation limited to ≤10

**Data Access Strategy**: Knot Atlas bulk download preferred; if per-knot API required, will implement rate-limiting (1 request/second) and pagination to complete within a reasonable CI budget.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility (NON-NEGOTIABLE) | PASS | Random seeds pinned in code; external datasets fetched from canonical source (Knot Atlas); `requirements.txt` pins all dependencies |
| II. Verified Accuracy | PASS | All external citations (Knot Atlas, KnotInfo, OEIS) will be validated by Reference-Validator Agent; title-token-overlap threshold ≥0.7 enforced. **Validation Independence Caveat**: Knot Atlas and KnotInfo both derive from Hoste-Thistlethwaite-Weeks enumeration; validation is consistency check, NOT independent verification. |
| III. Data Hygiene | PASS | All files under `data/` will be checksummed (SHA-256); no data modified in place; all transformations produce new files with documented derivation |
| IV. Single Source of Truth | PASS | Every figure/statistic traces back to exactly one row in `data/` and one block in `code/`; derived numbers will NOT be hand-typed into paper |
| V. Versioning Discipline | PASS | Every artifact carries content hash; Advancement-Evaluator Agent invalidates stale review records when artifacts change |
| VI. Mathematical Invariant Consistency | PASS | Computed invariants (braid index, arc index, Seifert circle count, bridge number) will be verified against primary mathematical literature; discrepancies documented with derivation notes. **Phase 1 Scope**: Only crossing number and braid index computed in Phase 1; arc index, Seifert circle count, bridge number deferred to Phase 2+ per FR-003. |
| VII. Statistical Significance Thresholds | PASS | All statistical claims include explicit thresholds (p-values, confidence intervals) and effect size measures; both Pearson and Spearman reported where distribution assumptions uncertain |

## Multicollinearity Strategy

**Mathematical Constraint**: Braid index ≤ crossing number is a known mathematical constraint, not an empirical finding. This creates a definitional relationship that must be acknowledged in all analysis.

**VIF Expectation**: Variance Inflation Factor (VIF) will be high by design due to predictor structure. Document VIF values as expected consequence; alternative methods (ridge regression, PCA) noted for consideration but not mandatory given census data context.

**Joint Regression Purpose**: Joint regression answers a variance partitioning question rather than independent explanatory power. This distinction will be clearly stated in all final reports.

## Census Data Limitations

**p-Value Treatment**: Since dataset represents complete census of prime knots ≤13 crossings, all statistical analysis is descriptive rather than inferential. Effect sizes are primary metrics. p-values may be documented for reporting convention but MUST NOT support inferential claims. This acknowledgment will appear in a single consolidated 'Census Data Limitations' section to avoid redundancy.

**Selection Bias**: Filtering to knots with valid hyperbolic volume (volume > 0) means the research question about 'prime knots' cannot be fully answered—only 'hyperbolic prime knots' are analyzed. All final reports MUST acknowledge this limitation explicitly.

## Project Structure

### Documentation (this feature)

```text
specs/010-quantifying-the-complexity-of-knot-diagr/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/
├── code/
│   ├── __init__.py
│   ├── download.py              # Knot Atlas data download with retry logic
│   ├── parse.py                 # Dataset parsing and cleaning
│   ├── invariants.py            # Additional invariant computation (Phase 2+)
│   ├── analysis.py              # EDA, regression, residual analysis
│   └── reproducibility.py       # Checksum, logging, seed management
├── data/
│   ├── raw/                     # Unmodified downloaded data
│   ├── processed/               # Cleaned/derived datasets
│   └── plots/                   # Generated visualization files
├── docs/
│   └── reproducibility/         # Checksums, derivation notes, logs, validation reports
├── tests/
│   ├── contract/                # Schema validation tests
│   ├── integration/             # Pipeline integration tests
│   └── unit/                    # Unit tests for individual functions
├── requirements.txt             # Pinned Python dependencies
└── README.md                    # Project overview and execution instructions
```

**Structure Decision**: Single computational research pipeline with modular separation of concerns (download, parse, analyze, reproducibility). No web/mobile components; all artifacts are files under `data/` and `docs/reproducibility/`. Tests organized by contract/integration/unit to match Constitution Principle I (reproducibility) and Principle III (data hygiene).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed with all 7 principles | No violations requiring justification |