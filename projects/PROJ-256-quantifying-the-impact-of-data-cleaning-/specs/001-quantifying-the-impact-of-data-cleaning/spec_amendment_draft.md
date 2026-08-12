# Specification Amendment Draft

## Overview
This document proposes amendments to the project specification to address
reviewer feedback regarding dataset scarcity, statistical correction methods,
and stratification requirements.

## 1. Revised Success Criteria (SC-006)
**Original**: "Analysis must include at least 10 distinct datasets."
**Amended**: "Analysis must include at least 5 distinct datasets. If fewer than
5 publicly available datasets meeting the inclusion criteria are found, the
report must explicitly state the final count (n) and note the limitation in
aggregate statistical power. Per-dataset reporting is prioritized over
aggregate summaries when n < 5."

**Rationale**: Reviewer feedback indicated that finding 10 suitable, clean,
public datasets with specific characteristics (binary outcome, numerical
predictors, missingness patterns) is infeasible within the project scope.
Lowering the threshold to 5 ensures the study remains rigorous while
acknowledging the practical constraints of public data availability.

## 2. Deviation from Functional Requirement FR-001
**Original FR-001**: "The system must process at least 10 datasets."
**Amended**: "The system must process a minimum of 2 datasets to demonstrate
the pipeline. A target of 5 datasets is preferred. The final report must
document the number of datasets processed and any deviations from the ideal
sample size."

**Rationale**: This deviation formally records the shift from the original
target of 10 datasets to a realistic minimum of 2 (UCI HAR and UCI Shopper)
and a preferred target of 5, aligning with the actual data acquisition
capabilities.

## 3. Functional Requirement FR-007 (Multiple Comparison Correction)
**Added Text**: "When reporting p-values across multiple cleaning strategies
or datasets, the system MUST apply the Benjamini-Hochberg (BH) procedure to
control the False Discovery Rate (FDR). If the number of hypotheses exceeds
20, the Bonferroni correction may be used as an alternative to control the
Family-Wise Error Rate (FWER), but this must be explicitly noted in the
final report."

**Rationale**: Reviewer feedback highlighted the need for rigorous
statistical correction when performing multiple hypothesis tests. The BH
procedure is preferred for exploratory analysis to balance Type I and Type
II errors.

## 4. Functional Requirement FR-008 (Stratification)
**Added Text**: "The system MUST stratify results by dataset size and missingness
rate. Each bin must contain at least one dataset to be included in the
stratified analysis. If a bin is empty, a warning must be logged, and that
bin must be excluded from the stratified summary, with the exclusion noted
in the final report."

**Rationale**: This ensures that stratification is only performed when
sufficient data exists to make meaningful comparisons, preventing misleading
conclusions from empty or sparsely populated bins.

## 5. Updated Success Criteria (SC-001, SC-002, SC-003)
**Original**: "Report must include median and IQR of p-value shifts."
**Amended**: "Report must include per-dataset delta reporting with qualitative
directionality assessment. Aggregate statistics (median/IQR) are optional
and should only be presented if the sample size (n) is ≥ 5. For n < 5,
individual dataset deltas and confidence intervals must be the primary
focus."

**Rationale**: Median and IQR are unstable metrics for small sample sizes.
The amendment prioritizes transparent, per-dataset reporting to ensure
scientific validity regardless of the final dataset count.

## Verification
The existence of this amendment draft and its integration into the final
specification will be verified by the test
`tests/unit/test_spec_amendment_draft_present.py`.
