# Downstream review concerns (address in this revision)

A downstream convergence panel kicked this project back to the idea stage. You MUST revise the idea — especially the `Methodology sketch` — to RESOLVE each concern below, not merely re-state the idea.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'science'. Routing to 'flesh_out_in_progress' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-008 states the system must perform a bootstrap “using a sufficient number of resamples” but does not specify how many resamples are required. Without a concrete number (e.g., 5,000 iterations as mentioned in the acceptance scenario), the requirement is ambiguous and cannot be deterministically verified.
- Specify the exact number of bootstrap resamples in FR-008 (and remove the `[deferred]` marker). Without a fixed count the bootstrap procedure cannot be reproducibly executed or its convergence assessed.
- FR-008 does not state the exact number of bootstrap resamples (e.g., 5,000) nor the format of the reported confidence interval, leaving the bootstrap procedure untestable.
- The specification still asserts that the OSF dataset at `https://osf.io/2g7h9/download` includes post‑feedback anxiety, rumination, and self‑efficacy measures. Public documentation of this dataset indicates those outcome variables are absent, so the primary moderation analysis cannot be performed with the stated data source. The revision’s response merely states the description was aligned with a new URL, but the URL remains unchanged and no evidence is provided that the dataset now contains the required variables. This concern remains unaddressed.
