# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan specifies a Wilcoxon signed‑rank test for the paired‑fold significance assessment, while the specification (FR‑012) requires a paired *t‑test*. This mismatch creates a methodological inconsistency that could affect the interpretation of the incremental predictive value.
- Feature selection (variance‑threshold, chi‑square top‑500, optional PCA) and hyper‑parameter tuning are described as separate pipeline steps but are not explicitly nested inside the cross‑validation loop. Performing these steps on the full dataset before CV introduces data‑leakage and inflates performance estimates.
- Power analysis is performed *after* the data are collected and models trained, and the plan merely notes any insufficiency in the final report. There is no mechanism to ensure that each species‑antibiotic pair meets the required sample size (≈ 1 400 isolates for d = 0.1, 80 % power) before proceeding, risking under‑powered conclusions.
- The plan filters isolates by core‑genome coverage and class balance but does not address other potential confounders such as geographic origin, collection date, or sequencing platform, which could correlate with both genotype and phenotype and bias the predictive assessment.
