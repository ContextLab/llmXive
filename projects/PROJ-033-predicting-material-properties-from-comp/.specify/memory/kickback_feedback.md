# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The central research question—quantifying performance loss when crystal‑structure information is excluded—requires a structure‑aware baseline. The plan defers FR‑005 and FR‑006 (structure‑aware graph construction and performance gap calculation) because no open CIF dataset is available, yet later sections (e.g., FR‑006 in the spec) still assert that ΔR² will be reported. This makes the primary claim untestable with the proposed methodology.
- FR-005 (structure‑aware graph construction) is marked as **deferred** and no implementation task is provided, leaving the functional requirement unaddressed.
- FR-006 (calculate metrics and ΔR² between composition‑only and structure‑aware models) is also deferred; the plan does not include any task to compute the performance gap.
- SC-002 (measurement and reporting of the ΔR² performance gap) cannot be satisfied because the structure‑aware baseline is omitted; the plan provides no alternative metric to fulfill this success criterion.
- The plan defers the structure‑aware baseline (FR‑005, FR‑006) because no open CIF dataset is available, yet the core scientific claim (quantifying information loss when crystal structure is excluded) and success criterion SC‑002 require a ΔR² comparison between composition‑only and structure‑aware models. Without this baseline the primary research question cannot be empirically answered, making the study scientifically incomplete.
