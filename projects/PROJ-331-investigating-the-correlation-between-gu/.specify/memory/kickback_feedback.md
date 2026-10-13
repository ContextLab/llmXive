# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The primary outcome (UPDRS III longitudinal slope) is not present in any verified dataset (see research.md). The plan proceeds under the assumption that this variable will be supplied later, which means the core research question cannot be answered with the currently available data.
- The plan assumes the presence of UPDRS III scores for each patient (e.g., computing per‑patient UPDRS III slopes), but `research.md` explicitly states that UPDRS III is not available in any verified PPMI dataset. This makes FR‑004 impossible to satisfy without an additional data source, violating the functional requirement and the project's data‑availability assumptions.
- The primary outcome variable (UPDRS III scores) is declared missing in the verified PPMI datasets (see research.md) yet the plan proceeds to compute per‑patient UPDRS III slopes and to validate taxon‑slope associations against them. Without a source for UPDRS III the validation target is undefined, making the core hypothesis untestable. The plan must either secure a verified source for longitudinal UPDRS III data or redesign the analysis to use an available proxy outcome.
