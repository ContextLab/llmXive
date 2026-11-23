# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Tasks T017-T019 implement `dlogz` convergence checks for `dynesty`, while spec.md FR-004 explicitly mandates a 'Gelman-Rubin statistic < 1.01' check. The tasks silently relax the spec's specific acceptance criterion (lexical requirement) to a different algorithm's metric without a spec amendment, violating FR-012 and the 'No weakening of FRs' principle.
