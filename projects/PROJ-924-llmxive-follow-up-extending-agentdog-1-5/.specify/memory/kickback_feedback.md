# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Under-reach vs idea: the idea specifies 3 annotators labeling each log as 'novel attack'/'known attack'/'benign' and stratifying into top-20%/bottom-20% drift bins, plus a chi-squared test of novel-label distribution across bins. The spec's US-02 omits annotator count, the three-way label scheme, the 20% stratification quantiles, and the chi-squared test (replaced by logistic regression + Mann-Whitney without justification).
