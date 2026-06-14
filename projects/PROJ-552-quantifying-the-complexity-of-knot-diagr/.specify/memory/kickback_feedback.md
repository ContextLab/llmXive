# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'writing'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Project Structure shows plots under data/processed/plots/ but spec.md FR-004 and quickstart.md Step 4 specify data/plots/ directory. Output paths should be consistent across documents.

## MAINTAINER DECISION — plan stage (path consistency)

The plan's Project Structure shows plots under `data/processed/plots/`,
but spec.md FR-004 and quickstart.md Step 4 specify `data/plots/`. The
SPEC is authoritative: use `data/plots/` for all plot outputs everywhere
in plan.md (Project Structure, any task/step references). Do not place
plots under data/processed/.
