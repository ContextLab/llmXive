# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- SC-003 specifies Monte Carlo validation threshold ≤ 0.01, while SC-026 specifies ≤ 0.005 for the same validation. FR-026 states ≤ 0.005. These conflicting thresholds create ambiguity about which success criterion applies.
- FR-002 references 'data-model.md' and 'extracted_summary.schema.yaml' which are external files not included in the spec. Cross-references should either be self-contained or clearly indicate external dependencies.
- FR-030 cites 'Kohavi et al. (2020)' but the reference section only contains a brief note without full bibliographic details. Constitution Principle II requires verified citations with title-token-overlap ≥ 0.7.
- SC-003 specifies Monte Carlo validation threshold ≤ 0.01, but FR-026 specifies ≤ 0.005. This creates an untestable contradiction — which threshold governs verification?
- FR-026 mandates Monte Carlo validation with 10,000 replicates, but SC-003 (the corresponding success criterion) uses a different threshold (0.01 vs 0.005). SC-026 references FR-026 but does not resolve the threshold conflict.
