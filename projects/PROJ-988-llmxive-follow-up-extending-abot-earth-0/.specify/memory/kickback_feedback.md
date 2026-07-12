# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-003 and SC-001 require an end-to-end pipeline that generates baseline 3DGS scenes AND applies inpainting to measure improvement. Tasks T021 (baseline) and T022 (inpainting) are split without a task explicitly orchestrating the full 'degraded input → baseline → inpainted output' flow required to compute the recovery rate.
- Consumer before Producer: T021 (baseline 3DGS) and T022 (inpainting) are listed as separate tasks, but the spec (FR-003, SC-001) requires an end-to-end pipeline where the inpainting module consumes the baseline 3DGS output to measure recovery. There is no task explicitly orchestrating the 'degraded input → baseline → inpainted output' flow, breaking the artifact dependency chain required for SC-001.
- Missing Producer for Success Criteria: SC-003 requires measuring peak RAM and wall-clock time per scene. T023 handles OOM errors but does not include a task to instrument, capture, and log these specific performance metrics to a file (e.g., `data/results/performance_log.csv`). Without this producer, the consumer (analysis of SC-003) has no data.
