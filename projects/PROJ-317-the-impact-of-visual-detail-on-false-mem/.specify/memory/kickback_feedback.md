# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T000 (Resolve Design Mismatch) is marked as FAILED/rejected, yet downstream tasks (T012-Design, T012-Runtime, T035a) explicitly depend on a 'Repeated-Measures' design and 'Repeated-Measures ANOVA' which contradicts the current plan.md (Between-Subjects/One-Way ANOVA). The task order implies execution can proceed despite a known, uncorrected contradiction in the foundational design document. A consumer task (T012-Design) cannot validly depend on a producer state (Plan) that is explicitly flagged as incorrect and unupdated.
- Task T006.3-Retry (Retry Logic) is listed as a dependency for T006.3-Complete, but T006.3-Select is the primary task. The description says 'If T006.3-Select fails...'. The ordering should clarify that T006.3-Complete depends on the *success* of either T006.3-Select OR the successful completion of the T006.3-Retry loop, not just T006.3-Select. The current dependency list 'Dependency: T006.3-Select or T006.3-Retry' is ambiguous in a linear task list.
