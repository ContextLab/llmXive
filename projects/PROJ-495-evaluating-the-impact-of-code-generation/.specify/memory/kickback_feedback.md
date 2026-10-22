# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 7 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan adjusts vulnerability counts only for false‑positive rates. False‑negative rates (missed vulnerabilities) are measured via precision/recall in the audit but never used to correct counts, risking systematic under‑counting that may differ between LLM‑generated and human code and thus bias the density comparison.
- Power is assessed only post‑hoc after data ingestion. No a priori sample‑size calculation is provided, so the study may proceed with insufficient observations, leading to under‑powered hypothesis tests and inconclusive results.
- Phase 3 (Deduplication) performs duplicate‑CWE collapsing but the implementation table does not list any FR or SC it satisfies. Deduplication is required by FR‑002 (deduplication of identical findings), so the plan should annotate that Phase 3 addresses FR‑002.
- Phase 4 (Complexity Proxy) computes cyclomatic complexity, yet the table omits any FR/SC linkage. The complexity proxy is a predictor in FR‑004 (NB regression covariate), so the plan should note that Phase 4 addresses FR‑004.
- Phase 10 (Instrumentation) uses psutil to capture runtime and memory, but the table does not reference SC‑003 or SC‑004, which set limits on execution time and RAM. The plan should indicate that Phase 10 satisfies SC‑003 and SC‑004.
- The plan cites the CodeVulnBench and Juliet Test Suite datasets but provides no verified URLs or checksums (the Constitution Check marks II. Verified Accuracy as **FAIL**). FR‑001 requires downloading datasets from publicly reachable, checksum‑verified sources; without verified citations the ingestion phase will abort, making the entire analysis infeasible.
- The plan produces `statistical_tests.csv` (Phase 6) but does not generate an artifact that conforms to the `aggregate-results.schema.yaml` contract (which expects a combined `groups` and `tests` array). Add a step that aggregates `group_summary.csv` and `statistical_tests.csv` into a single `aggregate_results.{json|yaml|csv}` file and validates it against `aggregate-results.schema.yaml`.
