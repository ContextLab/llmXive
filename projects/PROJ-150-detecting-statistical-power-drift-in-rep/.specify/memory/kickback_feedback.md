# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T020 is marked `[ ]` (unchecked) but also contains `<!-- FAILED: unspecified -->`. The presence of a failure flag on an unchecked task is confusing and suggests a stale state from a previous iteration that wasn't cleaned up.
- T020b is marked `[ ]` (unchecked) and contains `<!-- FAILED: unspecified -->` twice. This is a documentation inconsistency that needs resolution.
- T027 is marked `[ ]` (unchecked) but contains `<!-- FAILED: unspecified -->`. The failure flag on an unchecked task is a documentation error.
- T011b (Grouping Validation) is marked as 'FAILED: unspecified' in the task list, yet T011c (Model Fitting) explicitly depends on it ('Dynamically construct the random effects formula... to exclude groups flagged as... by T011b'). If T011b is not implemented or its output is undefined, T011c cannot correctly implement the 'Edge Cases' requirement for handling single-level groups. The ordering is correct (T011b before T011c), but the dependency is critical and the 'FAILED' status indicates the producer artifact is missing, blocking the consumer.
- T011c description states: 'Fit the primary LMM... Output: ... results/lmm_final_summary.json'. However, the task also includes 'Execute Likelihood-Ratio Test (LRT)' and 'Extract Primary Metrics'. This conflates model fitting, hypothesis testing, and result extraction into one task. While not a hard ordering violation, it makes the dependency graph for T013 (Visualization) and T020 (Permutation) ambiguous. T013 needs the summary JSON; T020 needs the slope. If T011c is atomic, the dependency is fine, but the task description should clarify that the JSON is the definitive output artifact for downstream consumers.
