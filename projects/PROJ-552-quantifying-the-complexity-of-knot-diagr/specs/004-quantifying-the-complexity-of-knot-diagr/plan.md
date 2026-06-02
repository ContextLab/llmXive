# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-02 | **Spec**: `specs/001-knot-complexity-analysis/spec.md`
**Input**: Feature specification from `/specs/001-knot-complexity-analysis/spec.md`

## Summary

This project quantifies the complexity of prime knots by analyzing the joint predictive relationship between crossing number and braid index for hyperbolic volume. Phase 1 focuses on the alternating/non-alternating dichotomy with validated completeness for crossing number ≤10 (data collected for ≤13). The technical approach involves downloading knot data from Knot Atlas, computing additional invariants (arc index, Seifert circle count, bridge number), fitting multiple regression models, and constructing a composite complexity score with extensive reproducibility documentation.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: pandas, scikit-learn, matplotlib, seaborn, requests, pyyaml, datasets (HuggingFace)
**Storage**: Local filesystem (data/, docs/, code/)
**Testing**: pytest with contract tests
**Target Platform**: Linux server (GitHub Actions runner)
**Project Type**: computational research / data analysis pipeline
**Performance Goals**: Complete analysis of ≤13 crossing number knots (9,988 at c=13) within 2 hours
**Constraints**: Retry logic for API failures (exponential backoff 1s→60s), ≥95% data completeness, ≥95% algorithm validation match threshold
**Scale/Scope**: ~10,000 prime knots, 3 regression models, 3 additional invariants computed, extensive reproducibility documentation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Action |
|-----------|--------|----------------------|
| I. Reproducibility (NON-NEGOTIABLE) | ✅ PASS | Random seeds pinned in code (FR-009); external datasets fetched from canonical source; `requirements.txt` at `code/`; end-to-end runnable notebooks/scripts |
| II. Verified Accuracy | ✅ PASS | All external citations verified against primary sources before contributing review points; title-token-overlap ≥0.7 threshold enforced by Reference-Validator Agent |
| III. Data Hygiene | ✅ PASS | All files under `data/` checksummed (SHA-256); raw data preserved unchanged; transformations produce new files with documented derivation; PII scan enforced |
| IV. Single Source of Truth | ✅ PASS | Every figure/statistic traces to exactly one row in `data/` and one block in `code/`; derived numbers not hand-typed into paper |
| V. Versioning Discipline | ✅ PASS | Every artifact carries content hash; Advancement-Evaluator invalidates stale review records when hashed artifact changes |
| VI. Mathematical Invariant Consistency | ✅ PASS | Computed invariants (crossing number, braid index, arc index, Seifert circle count, bridge number) verified against established definitions; discrepancies documented with derivation notes |
| VII. Statistical Significance Thresholds | ✅ PASS | All statistical claims include p-values, confidence intervals, and effect size measures; BOTH Pearson AND Spearman reported where distribution assumptions uncertain (FR-008) |

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
src/
├── models/
│   ├── __init__.py
│   ├── knot_record.py      # KnotRecord entity definition
│   └── regression_model.py # RegressionModel entity definition
├── services/
│   ├── __init__.py
│   ├── data_download.py    # Knot Atlas download with retry logic
│   ├── invariant_computation.py  # Arc index, Seifert circles, bridge number
│   ├── exploratory_analysis.py   # Scatter plots, stratification
│   └── regression_analysis.py    # Model fitting, composite score
├── cli/
│   └── __init__.py         # CLI entry points for pipeline stages
└── lib/
    ├── reproducibility.py  # Checksum, logging, seed pinning utilities
    └── validation.py       # Algorithm validation against KnotInfo

tests/
├── contract/
│   ├── test_knot_data_schema.py
│   └── test_regression_output_schema.py
├── integration/
│   └── test_pipeline.py
└── unit/
    ├── test_invariant_computation.py
    └── test_retry_logic.py

data/
├── raw/                    # Downloaded data (unchanged)
├── processed/              # Derived datasets
└── plots/                  # PNG output (1200x900 minimum)

docs/
└── reproducibility/
    ├── checksums.md
    ├── derivation_notes.md
    ├── logs/
    ├── algorithm_validation.md
    ├── tie_breaking_rules.md
    ├── validation_scope.md
    └── excluded_knots.md

config/
└── complexity_weights.yaml # Composite score weight configuration
```

**Structure Decision**: Single project structure (Option 1) selected as this is a computational research pipeline without frontend/backend separation. All code resides under `src/` with tests, data, and documentation in separate top-level directories. This enables end-to-end reproducibility on a single runner per Constitution Principle I.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 3 additional invariants (arc index, Seifert circle count, bridge number) | FR-003 requires exploratory extension beyond core crossing number/braid index analysis | Core research question focuses on crossing number + braid index predicting hyperbolic volume; additional invariants enable richer analysis but are not strictly required for MVP |
| Composite complexity score | FR-006 requires exploratory construct for joint predictive analysis | Original research question asked about joint predictive relationships; composite score enables quantification but has no established mathematical basis (acknowledged in spec) |
| Retry logic with exponential backoff | FR-010 requires robustness against API unavailability | Simple retry would fail on rate-limited scenarios; exponential backoff ensures resilience without excessive load |
