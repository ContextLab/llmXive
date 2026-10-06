# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T055 (IRR gate) depends on T033 (outlier removal) in the description ('Must run on raw data before T033'), but the dependency list says 'Must run on raw data before T033' while the task order places T055 BEFORE T033. This is a direct contradiction: the text says T055 runs BEFORE T033, but the dependency logic for outlier removal (T033) usually requires the IRR gate to pass first to ensure the data is reliable before cleaning. If T055 is the gate, it must run on the raw data *before* any cleaning (T033). The text 'Must run on raw data before T033' is correct, but the dependency arrow in the task list might be misinterpreted. Wait, the text says 'Must run on raw data before T033', and T055 is listed before T033. This is actually correct ordering. Re-evaluating: T055 (IRR) -> T033 (Outliers) -> T057b (Sensitivity) -> T060 (Test). This flow is correct. The concern is invalid. Removing.
- Task T072 (Blind Metadata Stripping) is in Phase 11 (Review-Driven Revisions) but depends on T059a (Blind Distribution) which is in Phase 5. T059a is marked [ ] (pending). T072 is a refinement of T059a. The ordering is acceptable as a revision, but T059a must be completed before T072 can be implemented. The current state has T059a pending and T072 pending, which is fine. No violation.
- Task T073 (Real Data Ingestion Trigger) depends on T065-trigger. T065-trigger is in Phase 5. T073 is in Phase 11. This is a revision. No violation.
- Task T074 (Expert Domain Validation) depends on T065-auto. T065-auto is in Phase 5. T074 is in Phase 11. This is a revision. No violation.
- Task T065-auto (recruitment) depends on T059a (blind distribution). T059a is pending. T065-auto is pending. This is correct. However, T065-trigger depends on T065-auto. T065-real depends on T065-trigger. T030-real depends on T065-real. T030a (ORCID) is complete. The flow is: T059a -> T065-auto -> T065-trigger -> T065-real -> T030-real. This is correct. No violation.
