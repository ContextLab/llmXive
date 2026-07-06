# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 4 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T039 (Full pipeline integration test) depends on T026 and T034. T026 (US2 output) and T034 (US3 output) are in different phases. Ensure T039 is strictly ordered after the completion of Phase 5 (T034) and Phase 4 (T026) in the execution logic, not just listed in Phase 6.
- T015 requires ingesting 'REAL transient-absorption spectroscopy data from data/raw/*.csv' but the plan explicitly states the approach uses 'simulated transient-absorption data'. The task provides no mechanism to acquire real data (e.g., instrument connection, file upload path, or dataset URL), making it impossible to execute deterministically without external context.
- T030b mandates performing ANOVA and reporting exact p-values, but the plan (Phase 3) explicitly states to 'Avoid p-value significance testing due to low N'. The task description does not resolve this contradiction or specify how to generate the required 'exact p-value' artifact if the plan forbids the calculation method.
- T042 introduces 'NMR' as an analytical method for product quantification. The spec (Assumptions and US-3) only authorizes 'HPLC with UV detection'. Introducing NMR constitutes a silent constitution drift by adding an unverified instrument capability and scope not present in the spec.
