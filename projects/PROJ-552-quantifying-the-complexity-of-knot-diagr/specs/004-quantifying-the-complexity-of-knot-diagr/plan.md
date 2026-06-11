# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-05-31 | **Spec**: `specs/004-quantifying-the-complexity-of-knot-diagr/spec.md`
**Input**: Feature specification from `/specs/004-quantifying-the-complexity-of-knot-diagr/spec.md`

## Summary

Phase 1 implementation focuses on quantifying knot complexity through crossing number and braid index analysis for prime knots with crossing number ≤10 (validated) and ≤13 (downloaded). The technical approach involves downloading knot data from KnotInfo/HTW GitHub, computing additional invariants (arc index, Seifert circle count, bridge number), performing exploratory analysis with stratified scatter plots, fitting multiple regression models to associate with hyperbolic volume, and constructing a composite complexity score with statistical validation.

**Note on Data Source**: Knot Atlas wiki lacks documented bulk API; using KnotInfo CSV export and Hoste-Thistlethwaite-Weeks enumeration on GitHub for stable bulk download.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scikit-learn, matplotlib, seaborn, requests, PyYAML, datasets, snappy, knotkit  
**Storage**: Local file system (data/, docs/reproducibility/)  
**Testing**: pytest  
**Target Platform**: Linux server (GitHub Actions runner)  
**Project Type**: research-analysis  
**Performance Goals**: Complete analysis [deferred] on standard runner
**Constraints**: Reproducible execution with pinned random seeds; no data modification in place  
**Scale/Scope**: the cumulative total of prime knots (crossing number ≤13 per OEIS A002863)

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

**Model Specifications**:
- Polynomial regression: maximum degree = 2
- Logarithmic regression: base e (natural log)
- Linear regression: ordinary least squares

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | PASS | Random seeds pinned in code; external datasets fetched from canonical sources (KnotInfo/HTW); requirements.txt pins all dependencies |
| II. Verified Accuracy | PASS | All citations will be validated against primary sources before publication; DOI references checked for reachability |
| III. Data Hygiene | PASS | All data files checksummed (SHA-256); no in-place modifications; derivations written to new files |
| IV. Single Source of Truth | PASS | All figures/statistics trace to exactly one row in data/ and one code block |
| V. Versioning Discipline | PASS | Content hashes for all artifacts; state file updated on changes |
| VI. Mathematical Invariant Consistency | PASS | Computed invariants verified against KnotInfo reference values where available |
| VII. Statistical Significance Thresholds | PASS | All statistical claims include p-values, confidence intervals, and effect sizes; both Pearson and Spearman reported |

## Project Structure

### Documentation (this feature)

```text
specs/004-quantifying-the-complexity-of-knot-diagr/
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
├── data/
│   ├── download_knot_data.py
│   ├── parse_knot_data.py
│   └── compute_invariants.py
├── analysis/
│   ├── exploratory_analysis.py
│   ├── regression_models.py
│   └── composite_score.py
├── utils/
│   ├── retry_utils.py
│   └── reproducibility_utils.py
├── tests/
│   ├── unit/
│   └── contract/
├── config/
│   └── complexity_weights.yaml
└── requirements.txt

data/
├── raw/
│   └── knot_atlas_export.csv
├── processed/
│   ├── invariants_dataset.parquet
│   └── exploratory_validation_sample.parquet
└── plots/
    └── crossing_vs_braid_stratified.png

docs/
└── reproducibility/
    ├── checksums.md
    ├── derivation_notes.md
    ├── logs/
    ├── algorithm_validation.md
    ├── excluded_knots.md
    ├── uncomputable_invariants.md
    ├── tie_breaking_rules.md
    ├── validation_status.md
    ├── validation_scope.md
    └── classification_counts.md
```

**Structure Decision**: Single project structure (Option 1) selected to match research-analysis workflow. All code under `code/` with data under `data/` and reproducibility documentation under `docs/reproducibility/`. This follows Constitution Principle III (Data Hygiene) by keeping raw data separate from processed data and derivations.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multiple regression model types (3+) | Required by FR-005 to test linear vs. non-linear relationships | Single model type would not capture potential non-linear patterns between invariants and hyperbolic volume |
| Composite complexity score construction | Enables exploration of joint predictive relationships beyond individual invariants | Individual invariants alone cannot test the hypothesis about joint prediction |
| Retry logic with exponential backoff | Required by FR-010 for KnotInfo availability resilience | Simple retry without backoff would cause rate-limiting failures |
| Comprehensive reproducibility documentation | Required by Constitution Principle I and FR-009 | Minimal documentation would not enable independent verification |
| Polynomial degree specification (max=2) | Required by methodology-57975f1a for construct validity | Undefined degree would allow arbitrary model selection |
| Knot-theory libraries (snappy, knotkit) | Required by data_resources-b38db894 for invariant computation | Standard ML libs cannot compute arc index, Seifert circles, bridge number |

## Task Implementation Matrix

| FR/SC ID | Implementation Element | File/Task | Output Artifact |
|----------|----------------------|-----------|-----------------|
| FR-010 | Retry logic with exponential backoff | code/utils/retry_utils.py | Retry verification log |
| SC-005 | Retry verification | code/utils/retry_utils.py | Pass/fail status |
| FR-013 | Tie-breaking rules documentation | docs/reproducibility/tie_breaking_rules.md | Tie-breaking policy |
| SC-008 | Tie-breaking validation script | code/data/parse_knot_data.py | Validation log |
| FR-014 | Hyperbolic volume filtering | code/data/parse_knot_data.py | excluded_knots.md |
| SC-014 | Excluded knots documentation | docs/reproducibility/excluded_knots.md | Exclusion log |
| SC-006 | Coverage metric computation | code/data/compute_invariants.py | uncomputable_invariants.md |
| SC-010 | Additional invariants (3+) | code/data/compute_invariants.py | Computed invariant fields |
| SC-012 | Algorithm validation | code/data/compute_invariants.py | algorithm_validation.md |
| SC-011 | ANOVA with effect sizes | code/analysis/exploratory_analysis.py | ANOVA results |
| SC-007 | Ambiguous classification handling | code/data/parse_knot_data.py | classification_counts.md |
| SC-013 | Validation scope documentation | code/data/parse_knot_data.py | validation_scope.md |