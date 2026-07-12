# Methodology Notes: Statistical Validation Approach

## Overview

This document explicitly documents the methodological decisions regarding statistical validation
for the LlmXive Follow-up project, specifically addressing the override of the original
specification requirements in favor of Constitution Principle VII.

## Override of Spec FR-006 (Binomial Test)

### Original Specification Requirement (FR-006)
The original project specification (FR-006) mandated the use of a **Binomial Test** for
validating classifier performance against a baseline.

### Constitution Principle VII Requirement
Constitution Principle VII explicitly requires the use of **McNemar's Test** for
comparing paired categorical predictions, particularly when evaluating whether a
classifier performs significantly better than a baseline.

### Decision
**Action Taken**: The Binomial Test (FR-006) has been **overridden** in favor of McNemar's Test.

**Justification**:
1. **Statistical Appropriateness**: McNemar's Test is specifically designed for paired nominal
 data (e.g., comparing two classifiers on the same test set), whereas the Binomial Test
 assumes independent trials and is less appropriate for this use case.
2. **Constitutional Compliance**: Constitution Principle VII takes precedence over the original
 specification. The Constitution serves as the governing framework for methodological choices.
3. **Baseline Comparison**: The test compares the proposed classifier against a **random-guessing
 baseline** (implemented via `DummyClassifier(strategy='stratified')` with a fixed seed),
 rather than a majority-class predictor. The majority-class baseline is addressed separately
 as a secondary verification (see T017a).

## Omission of Bonferroni Correction

### Original Specification Implication
The original specification (US-3) implied the use of multiple hypothesis testing corrections,
such as the Bonferroni correction, when evaluating performance across multiple thresholds
or metrics.

### Constitution Principle VII Guidance
Constitution Principle VII notes that when metrics are **dependent** (e.g., Recall and FPR
derived from the same confusion matrix, or performance at multiple thresholds from the same
model scores), applying strict Bonferroni correction may be overly conservative and reduce
statistical power without addressing the actual dependency structure.

### Decision
**Action Taken**: The Bonferroni correction is **omitted** for the primary validation metrics.

**Justification**:
1. **Dependent Metrics**: The metrics evaluated (Recall, FPR, AUC-ROC) are derived from the
 same underlying model predictions and are statistically dependent. Bonferroni correction
 assumes independence and would be inappropriate.
2. **Sensitivity Analysis**: Instead of correction, a **threshold sensitivity analysis** is
 performed (T022) across the set {0.3, 0.4, 0.5, 0.6, 0.7} to demonstrate the stability
 of results. This provides empirical evidence of robustness without requiring multiple
 testing corrections.
3. **Single Primary Test**: The primary statistical claim relies on a single McNemar's Test
 at the default threshold (0.5). The sensitivity analysis is exploratory and supports
 the primary finding rather than constituting additional independent hypotheses.

## Implementation Details

### McNemar's Test Implementation
- **Location**: `code/models/eval.py` (Task T018)
- **Baseline**: `DummyClassifier(strategy='stratified')` with fixed random seed
- **Threshold**: Default 0.5 (with sensitivity sweep)
- **Significance Level**: α = 0.05
- **Pass Condition**: p-value < 0.05 indicates the classifier performs significantly better
 than random guessing.

### Sensitivity Analysis
- **Location**: `code/models/eval.py` (Task T022)
- **Thresholds**: {0.3, 0.4, 0.5, 0.6, 0.7}
- **Output**: `results/sensitivity_report.md`
- **Documentation**: The report explicitly cites Constitution Principle VII and links to
 this document (T018b) as the justification for omitting Bonferroni correction.

## References

- **Constitution Principle VII**: Statistical testing methodology and baseline selection.
- **Task T018**: Implementation of McNemar's Test in `code/models/eval.py`.
- **Task T017a**: Implementation of Majority-Class Predictor Baseline (Secondary Verification).
- **Task T022**: Threshold sensitivity analysis on real data.
- **Task T022a**: Documentation of Bonferroni omission in sensitivity report.
- **Task T029a**: Amendment report detailing all specification deviations.

## Version Control

- **Date**: 2024 (Generated as part of Task T018b)
- **Project**: PROJ-835-llmxive-follow-up-extending-a-survey-of
- **Status**: Active Methodological Note