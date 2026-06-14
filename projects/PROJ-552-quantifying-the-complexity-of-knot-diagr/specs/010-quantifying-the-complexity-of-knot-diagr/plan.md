# Implementation Plan: Quantifying the Complexity of Knot Diagrams via Crossing Number and Braid Index

**Branch**: `001-knot-complexity-analysis` | **Date**: 2026-06-12 | **Spec**: `specs/010-quantifying-the-complexity-of-knot-diagr/spec.md`
**Input**: Feature specification from `specs/010-quantifying-the-complexity-of-knot-diagr/spec.md`

## Summary

This feature implements a computational pipeline to download, validate, and analyze knot invariant data from Knot Atlas for all prime knots with crossing number ≤ 13. The analysis focuses on correlating crossing number and braid index with hyperbolic volume as a measure of geometric complexity. Phase 1 validates completeness for crossing number ≤ 10 crossings; crossing number 11-13 data is downloaded and available for exploratory analysis only.

### Scope Qualification

**Validated Results**: All conclusions in the final paper will be qualified to the validated subset (crossing number ≤ 10 crossings). This includes all primary correlation coefficients, regression models, and effect size estimates.

**Exploratory Results**: Data for crossing number 11-13 will be downloaded and made available for exploratory analysis but will NOT be included in primary conclusions. Any analysis of 11-13 crossing knots will be clearly labeled as "exploratory only" with explicit caveats about validation status.

**Paper Structure**: The paper will contain separate sections for "Validated Results (≤10 crossings)" and "Exploratory Analysis (11-13 crossings)" to prevent conflation of validated vs. unvalidated findings.

### Selection Bias Qualification

**Filtered Scope**: The dataset is filtered to hyperbolic prime knots only (volume > 0), excluding torus and satellite knots per FR-012. This changes the scope from "prime knots" to "hyperbolic prime knots."

**Conclusion Qualification**: All final conclusions will explicitly state "hyperbolic prime knots" rather than "prime knots" to accurately reflect the analyzed population. The paper will include a "Limitations" section discussing the selection bias and its implications for generalization to non-hyperbolic knots.

**Alternative Analysis**: A secondary analysis will be conducted on the full prime knot dataset (including torus/satellite knots) to characterize how hyperbolic filtering affects correlation patterns. Results will be documented but not included in primary conclusions.

### Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, numpy, scipy, matplotlib, requests, pyyaml, datasets (HuggingFace)  
**Storage**: Local filesystem (data/, docs/reproducibility/)  
**Testing**: pytest with contract validation against YAML schemas  
**Target Platform**: Linux server (GitHub Actions-compatible)  
**Project Type**: computational research pipeline  
**Performance Goals**: Complete pipeline execution within 2 hours on standard CI resources  
**Constraints**: Must handle API unavailability with retry logic; all data transformations must be reproducible with pinned random seeds  
**Scale/Scope**: The total number of prime knots (OEIS A002863), with Phase 1 validation benchmark for ≤ 10 crossings

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Constitution Principle | Compliance Status | Evidence / Notes |
|------------------------|-------------------|------------------|
| **I. Reproducibility** | COMPLIANT | Random seeds pinned in code; external datasets fetched from canonical sources; `data/` files checksummed (SHA-256) with documentation in `docs/reproducibility/` |
| **II. Verified Accuracy** | COMPLIANT | All citations (Knot Atlas, KnotInfo, OEIS, arXiv:math/0303273, Schubert 1954) will be validated against primary sources before publication; Reference-Validator Agent runs at artifact write and advancement gates |
| **III. Data Hygiene** | COMPLIANT | No in-place modifications; all transformations produce new files with documented derivation notes; checksums recorded under `data/`; PII scan passes (no PII expected in knot data) |
| **IV. Single Source of Truth** | COMPLIANT | All figures/statistics trace to exactly one row in `data/` and one code block in `code/`; derived numbers auto-generated from data, not hand-typed |
| **V. Versioning Discipline** | COMPLIANT | All artifacts carry content hashes; Advancement-Evaluator invalidates stale review records on hash changes; state YAML updated on artifact changes |
| **VI. Mathematical Invariant Consistency** | COMPLIANT | Computed invariants (arc index via Birman-Menasco algorithm (arXiv preprint), Seifert circle count via Seifert's algorithm s(D) (arXiv preprint), bridge number via Schubert's decomposition (Schubert)) verified against primary mathematical literature; discrepancies documented with derivation notes |
| **VII. Statistical Significance** | COMPLIANT (census-data exception applies per FR-006) | Census-data exception applies: analysis covers complete census of prime knots ≤ 13 crossings (9988 knots, source: OEIS A002863); effect sizes (Cohen's d, r, r²) are primary metrics; p-values NOT reported for census data per Constitution Principle VII amendment |

**GATE STATUS**: PASS — All principles addressed; census-data exception to Principle VII explicitly documented in FR-006 and Assumptions.

**Note on Spec.md Citations**: The source specification (spec.md FR-003) contains unresolved citation placeholders that require separate correction. This plan uses the resolved citations from research.md (arXiv:math/0303273 for Seifert/Birman-Menasco, Schubert 1954 for bridge number) to ensure internal consistency of plan-stage artifacts.

## Project Structure

### Documentation (this feature)

```text
specs/010-quantifying-the-complexity-of-knot-diagr/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── knot_record.schema.yaml
│   ├── regression_model.schema.yaml
│   └── dataset.schema.yaml
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── download/
│   │   ├── __init__.py
│   │   └── knot_atlas_downloader.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── parser.py
│   │   ├── validator.py              # Includes FR-010 ambiguous classification handling
│   │   └── filter_hyperbolic.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── exploratory.py
│   │   ├── regression.py
│   │   ├── residual_analysis.py
│   │   └── knotinfo_crosscheck.py    # FR-013/SC-014 KnotInfo cross-check module
│   ├── reproducibility/
│   │   ├── __init__.py
│   │   ├── checksums.py
│   │   ├── logs.py
│   │   ├── validation_scripts.py
│   │   └── validation_scripts/
│   │       ├── tie_breaking_validator.py    # SC-007 tie-breaking validation
│   │       └── data_consistency_validator.py
│   └── main.py
├── data/
│   ├── raw/
│   │   └── knot_atlas_raw.json (downloaded, checksummed)
│   ├── processed/
│   │   ├── knots_validated.parquet
│   │   ├── knots_hyperbolic.parquet
│   │   └── plots/
│   ├── checksums.txt
│   └── reproducibility/
│       ├── data_quality_report.md
│       ├── validation_scope.md
│       ├── excluded_knots.md
│       ├── tie_breaking_rules.md
│       ├── random_seeds.md
│       ├── logs/
│       └── derivation_notes/
├── tests/
│   ├── contract/
│   │   ├── test_knot_record_schema.py
│   │   ├── test_regression_model_schema.py
│   │   └── test_dataset_schema.py
│   ├── integration/
│   │   └── test_download_pipeline.py
│   └── unit/
│       ├── test_parser.py
│       └── test_validator.py
└── docs/
    └── reproducibility/
        └── (symlinks to data/reproducibility/)
```

**Structure Decision**: Single computational research pipeline structure selected. All code under `code/` with isolated `requirements.txt` for reproducible virtualenv execution. Data under `data/` with raw/processed separation per Constitution Principle III. Reproducibility artifacts in `data/reproducibility/` with checksums, logs, derivation notes, and validation scripts as required by FR-007.

## Statistical Methodology

### Correlation Analysis

| Method | Primary Use | Justification |
|--------|-------------|---------------|
| Spearman correlation | Primary for discrete integer-valued invariants | Crossing number and braid index are small integers; discrete data limitations acknowledged |
| Pearson correlation | Supplementary for reporting completeness | Assumes continuous data with normal distribution; interpretation limited by discrete nature |

### Effect Size Measures (Census Data)

| Comparison Type | Effect Size Metric | Reporting Requirement |
|-----------------|-------------------|----------------------|
| Correlation | r or r² | Report for all correlations |
| Group comparison (alternating vs. non-alternating) | Cohen's d | Report mean differences, variance ratios, AND Cohen's d |
| Model fit | R², AIC, BIC | Descriptive fit statistics for finite census dataset |

### Multicollinearity Interpretation

**Mathematical Constraint**: Braid index ≤ crossing number is a known mathematical inequality, not an empirical finding. This creates a definitional relationship that must be acknowledged in all analysis.

**Coefficient Interpretation**: Joint regression coefficients represent variance partitioning within the finite census dataset, NOT independent explanatory power. All final reports MUST explicitly state this limitation to prevent misinterpretation.

**VIF Documentation**: Compute Variance Inflation Factor (VIF) for all joint regression models. Document VIF values as expected consequence of predictor structure (braid index ≤ crossing number). Results documented in `docs/reproducibility/multicollinearity_assessment.md`.

### Stratified Residual Analysis

**Structural Property Testing**: Residuals ≥ 2 standard deviations from fitted trend will be tested for structural patterns via stratified analysis:

| Stratification Variable | Test Method | Expected Outcome |
|------------------------|-------------|------------------|
| Alternating classification | Group comparison (Cohen's d) | Test if residuals differ by alternating/non-alternating status |
| Crossing number bands | ANOVA-like comparison | Test if residuals vary systematically by crossing number range |
| Braid index bands | Group comparison | Test if residuals vary by braid index strata |

**Unexplained Variance**: After stratified analysis, remaining residual variance will be characterized as "unexplained" with explicit acknowledgment that some variance may reflect: (1) measurement uncertainty in source databases, (2) knot families with atypical geometric properties, or (3) limitations of the linear model specification.

## Data Consistency Cross-Check (FR-013)

| Aspect | Requirement |
|--------|-------------|
| Reference | KnotInfo (https://knotinfo.org) — programmatic loading via web scraping with rate limiting |
| Threshold | ≥ 90% match against KnotInfo reference values where both available |
| Coverage | ≥ 90% coverage required; if < 90%, cross-check skipped and limitation documented |
| Source Independence Qualification | When Knot Atlas and KnotInfo share underlying data sources, high match rate reflects data lineage NOT independent accuracy confirmation. All final reports MUST explicitly state this limitation. Validation target (hyperbolic volume) and predictors (crossing number, braid index) are mathematically independent variables; shared sources imply dependent measurements, not dependent variables. |

**Implementation**: code/analysis/knotinfo_crosscheck.py will implement FR-013/SC-014 with dedicated validation output in `docs/reproducibility/data_consistency_report.md`.

**Note on Spec.md FR-013**: The source specification (spec.md FR-013) contains mathematically incorrect language about statistical independence. This plan uses the corrected language from research.md: "high match rate reflects data lineage NOT independent accuracy confirmation."

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Separate `data/reproducibility/` directory | Constitution Principle III requires checksums recorded under `data/` with documentation in `docs/reproducibility/`; FR-007 requires checksums, derivation notes, logs, random seeds in reproducible format | Single `docs/reproducibility/` would violate Principle III's requirement that checksums be under `data/` directory |
| Retry logic with exponential backoff (FR-008) | Knot Atlas API may be unavailable or rate-limited; FR-008 requires retry sequence with configurable delays | No retry logic would cause pipeline failure on transient network issues, violating Constitution Principle I (reproducibility) |
| Census-data exception to Principle VII | Dataset is complete enumeration of known prime knots (OEIS A002863), not a sample; p-values inapplicable | Standard inferential statistics (p-values, confidence intervals) would be statistically invalid for census data |
| KnotInfo cross-check module | FR-013/SC-014 requires ≥90% match validation with dedicated implementation | Ad-hoc validation would not satisfy reproducibility requirements; dedicated module ensures consistent execution |
| Tie-breaking validation script | SC-007 requires specific tie-breaking validation script to confirm consistency | Manual verification would not satisfy reproducibility requirements; automated script ensures consistent validation |

## Schema Validation

All data must pass validation against YAML schemas in `contracts/`:
- `contracts/knot_record.schema.yaml`: Validates individual KnotRecord entities
- `contracts/regression_model.schema.yaml`: Validates RegressionModel entities  
- `contracts/dataset.schema.yaml`: Validates InvariantsDataset aggregation metadata

Validation performed by pytest contract tests in `tests/contract/`.