# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan describes a synthetic‑benchmark fallback when no real RI dataset is found, but there is no corresponding task implementing this fallback step.
- Task T001 failed (download script exit = 1), so FR‑001 (dataset download & preprocessing) is not satisfied; verification condition cannot be met.
- The plan describes a synthetic‑benchmark fallback when no real RI dataset is found, but the spec’s FR‑001 requires a real curated dataset; introducing synthetic data without spec approval weakens the requirement.
- The synthetic‑benchmark fallback is mentioned in the plan but no corresponding task is defined in tasks.md, leaving the plan step orphaned and unimplemented.
