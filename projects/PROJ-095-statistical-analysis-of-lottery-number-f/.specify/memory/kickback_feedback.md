# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T012 ('join raw draws with calculated metrics') depends on T011 ('calculate_rolling_uniformity_deviation'). If T011 produces a rolling window metric (as described), T012 cannot correctly 'join' this to a single draw row without a specific aggregation logic (e.g., 'last 50 draws' vs 'current draw'). The task description is ambiguous about the output schema of T011, making the dependency on T012 semantically unsafe. The task order implies a direct join, but the data flow (rolling window -> single row) requires an explicit aggregation step missing from the task list.
