# Revision Notes

## Overview

This document tracks significant revisions and methodological changes to the project, particularly those driven by reviewer feedback.

## Revision 1: Tractography Noise Sensitivity (Phase 6)

**Date**: 2026-06-26
**Reviewer**: john-von-neumann-simulated
**Issue**: Concerns about false-positive rates in diffusion MRI tractography (Yeh et al., 2018) potentially driving spurious correlations.

### Changes Made

1. **Configuration Updates (T041)**
 - Added `TRACTOGRAPHY_CONFIDENCE_THRESHOLDS = [0.0, 0.2, 0.4, 0.6, 0.8]` to `code/config.py`
 - Extended structural data loader to accept `confidence_threshold` parameter

2. **Sensitivity Analysis Execution (T042)**
 - Implemented loop in `code/preprocess/structural.py` to iterate through confidence thresholds
 - Added `code/analysis/tractography_sensitivity.py` for dedicated sensitivity analysis
 - Output: `data/processed/tractography_sensitivity_metrics.csv`

3. **Correlation Sensitivity (T043)**
 - Implemented `code/analysis/tractography_correlation_sensitivity.py`
 - Re-ran US2 correlation analysis for each confidence threshold
 - Output: `data/processed/tractography_correlation_sensitivity.csv`

4. **Report Integration (T044)**
 - Updated `code/reports/generate_report.py` with "Tractography Noise Sensitivity" section
 - Explicitly cites Yeh et al., 2018 regarding false-positive rates
 - Shows how statistical power changes across confidence thresholds
 - Includes explicit warning if findings vanish at high confidence

### Methodological Rationale

Diffusion MRI tractography is known to have substantial false-positive rates. [UNRESOLVED-CLAIM: c_849a3a8f — status=not_enough_info] Without accounting for this, correlations between structural and functional metrics may be artifacts rather than genuine biological relationships.

By varying the confidence threshold, we can assess whether findings are robust to stricter (cleaner) structural data. If correlations disappear at high confidence thresholds, this suggests the original findings may be driven by tractography artifacts.

### Expected Outcomes

- **Robust findings**: Correlations persist across all confidence thresholds
- **Fragile findings**: Correlations weaken or disappear at high confidence thresholds
- **Report requirement**: Explicitly state if findings are fragile, acknowledging potential artifact

## Revision 2: Associational Language Compliance

**Date**: 2026-06-26
**Requirement**: FR-007, Constitution Principle VI
**Issue**: Research question initially used "predict" language implying causality.

### Changes Made

1. **Language Audit Tool**
 - Created `code/reports/audit_associational_language.py`
 - Automated scanning for causal verbs and phrases

2. **Documentation**
 - Added `docs/associational_language_guide.md`
 - Updated all reports to use "associated with" instead of "predicts"

3. **Research Question Refinement**
 - Original: "Do topological properties... predict the prevalence..."
 - Revised: "What is the association between topological properties... and the prevalence..."

## Revision 3: Leave-One-Out (LOO) Independence

**Date**: 2026-06-26
**Requirement**: Plan's "Independence Enforcement" section
**Issue**: FR-002's "common set" approach violates statistical independence.

### Changes Made

1. **LOO K-Means Implementation (T016)**
 - Centroids for subject `i` computed exclusively from subjects `j != i`
 - Ensures subject `i`'s data never used to generate its own centroids

2. **Verification Test (T013b)**
 - Unit test explicitly verifies LOO independence constraint
 - Asserts subject `i` excluded from centroid generation

3. **Documentation**
 - Added note in `docs/README.md` explaining LOO strategy
 - Documented deviation from FR-002 as intentional for statistical validity

## Revision 4: Window Length Validation

**Date**: 2026-06-26
**Requirement**: Constitution Principle VII, FR-008
**Issue**: Metric stability across different window lengths must be verified.

### Changes Made

1. **Configuration (T031-Setup-Config)**
 - `WINDOW_LENGTH_VALIDATION = [20, 25, 30, 35]`

2. **Execution (T031-Execute)**
 - Full re-run of dynamic metric extraction and correlation for each window length
 - Comparison against 30 TR baseline

3. **Output**
 - `data/processed/sensitivity_comparison.csv` with absolute differences in correlation coefficients

## Future Revisions

Potential areas for future revision:
- Alternative structural connectivity methods (to validate tractography findings)
- Larger cohort sizes for increased statistical power
- Longitudinal analysis (if data becomes available)
- Cross-validation of findings in independent datasets

## Revision Log

| Date | Version | Author | Description |
|------------|---------|-------------------------|--------------------------------------|
| 2026-06-26 | 1.0.0 | llmXive Pipeline | Initial release with all revisions |
| 2026-06-26 | 1.0.1 | llmXive Pipeline | Tractography sensitivity added |
| 2026-06-26 | 1.0.2 | llmXive Pipeline | Associational language compliance |