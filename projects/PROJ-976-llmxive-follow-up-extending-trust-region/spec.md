# Specification: Diversity Profiles for TRB Extension

## Functional Requirements
- **FR-001**: System must compute lexical diversity metrics (distinct-4, n-gram entropy).
- **FR-002**: System must compute syntactic diversity metrics (parse tree depth variance).
- **FR-003**: System must correlate diversity metrics with proxy targets (relevance, length).
- **FR-004**: System must validate generalization of correlations across domains.
- **FR-005**: System must operate without ground-truth collapse labels.

## Success Criteria
- **SC-001**: Correlation coefficients (|r| > 0.2, p < 0.05) between diversity and proxy targets.
- **SC-002**: Proxy FPR reported as substitute for collapse FPR (acknowledging scope gap).
- **SC-003**: Generalization gap < 0.15 between source and target domains.
- **SC-004**: Permutation test p-value < 0.05 for target correlations.

## Scope Gap Acknowledgement
Ground-truth collapse labels are unavailable. The system uses **proxy targets** (relevance scores, text length) to approximate collapse/stability.
"Proxy Collapse" = Low Relevance / High Length Variance.
"Proxy Stability" = High Relevance / Low Length Variance.
