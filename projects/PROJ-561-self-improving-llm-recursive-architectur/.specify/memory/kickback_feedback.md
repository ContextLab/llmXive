# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T015 (Parse Proposal) depends on T013, T006, T037. T015 is marked [US1] but not [P]. However, T016 (Apply Modification) depends on T013. T016 is marked [US1] but not [P]. T017a (Training Loop) depends on T008 (Config). T017a is not marked [P]. The ordering within US1 seems correct (T015 -> T016 -> T017a), but the dependency on T008 (Config) for T017a is critical. T008 is in Phase 2. If T008 is not completed before T017a, T017a will fail. The task list shows T008 in Phase 2, which is correct, but the [P] tag on T008 implies it can run in parallel with other Phase 2 tasks. This is fine, but T017a must wait for T008.
- Task T031 (Trade-off Metrics) depends on T030, T048. T031 is marked [US3] but not [P]. T030 (FLOPs Aggregation) depends on T017b. T030 is marked [US2] but not [P]. T048 (Resource Monitoring) depends on T004. T048 is marked [US3] but not [P]. T033 (Generate Analysis) depends on T031. T033 is marked [US3] but not [P]. The dependency chain T033 -> T031 -> T030/T048 is correct. However, T030 is in US2, T031 and T033 are in US3. This implies US3 depends on US2 completion, which is consistent with the 'User Story Dependencies' section. The [P] tags are correctly absent.
