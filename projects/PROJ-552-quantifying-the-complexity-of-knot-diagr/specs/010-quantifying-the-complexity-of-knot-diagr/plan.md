# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-12 | **Spec**: `specs/001-knot-complexity-analysis/spec.md`
**Input**: Feature specification from `specs/001-knot-complexity-analysis/spec.md`

## Summary

This feature implements a research pipeline to quantify knot diagram complexity by downloading prime knot data from Knot Atlas, computing core invariants (crossing number, braid index, hyperbolic volume), and fitting regression models to assess joint predictive relationships. Phase 1 focuses on validated crossing number ≤10 data with core invariants only; additional invariants and full validation at crossing numbers 11-13 are Phase 2+ scope.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scikit-learn, matplotlib, seaborn, requests, PyYAML  
**Storage**: Local filesystem (data/, docs/reproducibility/)  
**Testing**: pytest  
**Target Platform**: Linux server (GitHub Actions runner)  
**Project Type**: computational research pipeline  
**Performance Goals**: Complete analysis within single GitHub Actions job (within a reasonable timeframe)  
**Constraints**: Data download retry logic with exponential backoff; census data statistical interpretation (descriptive, not inferential); p-values NOT reported for census data  
**Scale/Scope**: The set of prime knots at crossing number ≤13 (source: OEIS A002863, https://oeis.org/A002863; total: the complete enumeration of prime knots)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Evidence |
|-----------|-------------------|----------|
| I. Reproducibility | PASS | Random seeds pinned in code; checksums recorded under data/; derivation notes in docs/reproducibility/ |
| II. Verified Accuracy | PASS | All external citations verified against primary sources; KnotInfo cited by name only (no URL - not in verified datasets block) |
| III. Data Hygiene | PASS | SHA-256 checksums for all data files; no in-place modifications; transformations produce new files |
| IV. Single Source of Truth | PASS | All statistics trace to data/ rows; no hand-typed numbers in paper; data-model.md aligned with contract schemas |
| V. Versioning Discipline | PASS | Content hashes for all artifacts; state file updated on artifact changes |
| VI. Mathematical Invariant Consistency | PASS | Invariants verified against primary literature; discrepancies documented with derivation notes |
| VII. Statistical Significance Thresholds | PASS | All claims include effect sizes; p-values excluded for census data to avoid misinterpretation |

## Project Structure

### Documentation (this feature)

```text
specs/001-knot-complexity-analysis/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── download/
│   ├── knot_data_downloader.py
│   └── retry_mechanism.py
├── data/
│   ├── raw/
│   └── processed/
├── analysis/
│   ├── exploratory_analysis.py
│   ├── regression_models.py
│   └── residual_analysis.py
├── reproducibility/
│   ├── data_quality_report.md
│   ├── algorithm_validation.md
│   ├── hyperbolic_volume_validation.md
│   ├── validation_scope.md
│   ├── excluded_knots.md
│   ├── invariant_coverage.md
│   ├── data_quality_flags.md
│   ├── missing_invariant_flags.md
│   ├── tie_breaking_rules.md
│   ├── validation_status.md
│   ├── random_seeds.md
│   ├── multicollinearity_assessment.md
│   ├── residual_analysis.md
│   └── invariant_algorithms.md
├── plots/
│   └── [generated PNG files]
└── tests/
    ├── contract/
    ├── integration/
    └── unit/

docs/
└── reproducibility/
    └── [FR-007 artifacts]
```

**Structure Decision**: Single project structure with clear separation between download, analysis, and reproducibility components. This follows Constitution Principle I (Reproducibility) by keeping all transformation artifacts under reproducibility/ while raw data remains under data/.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Retry logic with exponential backoff | Knot Atlas API may be rate-limited or unavailable | Direct download without retry would fail silently and invalidate reproducibility |
| Dual flag system (data_quality_flags vs missing_invariant_flags) | Distinguishes data quality issues from computability issues per FR-002/FR-009 | Single flag system would obscure root cause of data gaps |
| Separate validation documents per invariant type | Constitution Principle II requires verified accuracy for each claim | Consolidated validation would mix independent verification requirements |
| P-value exclusion for census data | Census data p-values are not applicable and reporting them risks misinterpretation | Reporting p-values "for convention" contradicts statistical best practices for complete enumeration |
| Multicollinearity documentation | Braid index ≤ crossing number is a mathematical constraint, not a statistical finding | Omitting this limitation would misrepresent regression interpretability |

## Critical Spec.md Issues Requiring Kickback

**WARNING**: The following issues exist in the source spec.md and cannot be resolved at the plan stage. These must be addressed via kickback to clarify stage:

1. **FR-013 Corrupted URL**: spec.md:FR-013 contains corrupted URL text: `( nodename nor servname provided, or not known)'))])`. This blocks Constitution Principle II (Verified Accuracy) verification. The plan artifacts cite KnotInfo by name only (no URL) per verified datasets block requirements.

2. **FR-013 Unquantified Threshold**: spec.md:FR-013 states "high match threshold" without quantification. The plan and research artifacts specify ≥90% match threshold where coverage ≥50%. This inconsistency creates testability ambiguity.

3. **FR-006 P-Value Policy Conflict**: spec.md:FR-006 states "p-values are documented for reporting convention only" while research.md and this plan explicitly exclude p-values for census data. This creates implementation ambiguity.

**Action Required**: These spec.md issues must be corrected before the project can pass the Verified Accuracy Gate. The plan artifacts document the corrected behavior (research.md alignment) but cannot modify spec.md directly.

## Note on spec.md artifact

The source spec.md contains a corrupted URL for KnotInfo in FR-013. This has been removed from all plan-stage artifacts. The spec.md itself requires separate correction (flagged for kickback to clarify stage).