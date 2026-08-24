# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T006 and T007 are marked [X] (completed) but T004 and T005 are not. This is inconsistent with the 'Foundational' phase description which implies all tasks in this phase must be complete before user stories. The [X] status suggests they are done, but the dependency logic for the rest of the plan assumes they are pending. This is a status inconsistency, not a strict ordering violation, but it confuses the execution flow.
- Task T013 (Ingest PDBbind) includes 'Power Analysis' and 'Sampling' to select N=1,000 complexes. Task T014 (Graph Construction) uses this sampled data. Task T020 (High-resolution filter) is listed AFTER T014. If T020 filters out complexes with resolution > 2.5 Å, it must happen BEFORE T014 (Graph Construction) to avoid constructing graphs for data that will be discarded. The current order (T013 -> T014 -> ... -> T020) implies graphs are built for all data, then filtered, which is inefficient and contradicts the 'before ingestion' requirement in T020's description. T020 must be a dependency of T014.
