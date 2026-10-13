# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T106 flags adapter records with injected_state='neutral-monitoring' as exclude_from_stats:true and T109/T110 filter them from the primary comparison. The spec's edge case says the neutral fallback exists to keep 'the static baseline comparison remain valid' — i.e., the neutral-monitoring run IS the valid adapter behavior for that trajectory, not a discardable record. One-sided post-hoc exclusion of adapter runs only breaks the paired design mandated by Constitution VII (same trajectories, same LLM, both conditions). No spec clause authorizes excluding these records from the primary effect.
