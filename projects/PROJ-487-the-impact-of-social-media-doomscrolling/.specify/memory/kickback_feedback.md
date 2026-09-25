# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The Plan mandates a 'Pilot validation step' for Google Trends keywords to verify stability (r > 0.7 against 'pandemic fear'). No task exists to perform this pilot validation or to implement the fallback keyword logic if the correlation threshold is not met.
- The Plan specifies using 'GDELT GKG 2.0 bulk download via AWS S3' for the full 2020-2023 range to avoid rate limits. Task T012 implements fetching via the 'GDELT 2.0 Event Database API' (EventQuery). There is no task to implement the bulk download strategy from AWS S3.
- The Plan requires 'Detrend/Seasonal Decompose' as a primary step for non-stationary data. Task T019a only handles differencing. The decomposition logic is missing from the tasks.
- Task T030a-ASSEMBLE depends on T030a-PLOTS and T030a-TEXT. T030a-TEXT creates a template file. T030a-PLOTS generates images. The dependency is valid. However, T030a-ASSEMBLE also depends on T029a and T029c (Statistical Report). T029c validates the JSON report. The order is correct (Generate -> Validate -> Assemble). No critical ordering violation here, but the task description for T030a-ASSEMBLE is dense and could be split for clarity.
