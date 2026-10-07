# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 8 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T049 (convergence_monitor) depends on T016 (glm_fitter), which is marked as unchecked. T049 cannot parse the `convergence_log.json` produced by T016 if T016 is not implemented. This blocks the execution monitoring for US2.
- Task T082 (contract test for data integrity) depends on T062. Since T062 is marked as unchecked (missing), T082 cannot be executed. This breaks the verification of the 'Fail Loudly' policy and data hygiene principles.
- Task T017 depends on T066 (data_leakage_guard). T066 is marked as unchecked (missing). The split-half validation logic (T017) explicitly requires the memory isolation provided by T066 to prevent data leakage. Without T066, T017 cannot safely execute the bootstrap loop as described.
- Task T070 (check_data_leakage unit test) depends on T066. T066 is unchecked. This test cannot be written or run without the implementation of the data leakage guard utility.
- Task T060 (enhance effect_size_extractor to log seed) depends on T031c. T031c depends on T016. T016 is unchecked. This breaks the traceability chain for the sensitivity analysis.
- Task T081 (sampling_strategy) depends on T079. T079 depends on T078. T078 depends on T005. T005 is checked. However, T081 is critical for the 'Real Sample' policy. The dependency chain is valid, but T081 is unchecked. This is a missing task, not a dependency error, but it blocks T086 and T075.
- Task T086 depends on T081. T081 is unchecked. This creates a dependency on an unimplemented task.
- Task T075 depends on T081. T081 is unchecked. This blocks the final integration test.
