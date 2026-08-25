# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 52 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T015 (ingest.py) has a dependency on T013 and T014. T013 and T014 are simulation tasks. T015 is the real data ingestion task. This implies the real data ingestion depends on simulation tasks, which is semantically incorrect. The real data path should depend on T054b and T041, not T013/T014. This is a semantic ordering violation.
- T061 (vr_mapping_logic.py) is a duplicate of T016b. T016b is in Phase 3 and depends on T044 (incomplete). T061 is also in Phase 3 and depends on T044. Having two tasks for the same logic creates ambiguity in the ordering and execution flow. One should be removed or merged.
- T011 (test_schema) depends on T007b (gervais_norms.yaml) and T008b (schema.py). Both are marked [X] (complete). T011 is marked [X] (complete). This is consistent.
- T012 (test_psychometric) depends on T007b (gervais_norms.yaml). T007b is complete. T012 is incomplete. Ordering is valid.
- T017 (validation logic) depends on T013 (simulation_mfq.py). T013 is incomplete. T017 is incomplete. Ordering is valid but blocked.
- T018 (hashing integration) depends on T006 (hashing.py). T006 is complete. T018 is incomplete. Ordering is valid but blocked by T013/T014/T016 which are blocked by T045/T044.
- T038 (unity_verification) depends on T044 (unity_blend_shapes.yaml). T044 is incomplete. T038 is incomplete. Ordering is valid but blocked.
- T056 (simulation.py) depends on T013, T014, T016. All are incomplete. T056 is incomplete. Ordering is valid but blocked.
- T060 (streaming_loader) depends on T054b (fetch_real.py). T054b is in Phase 6. T060 is in Phase 3. This is a forward dependency violation. T060 should be in Phase 6 or Phase 4.
- T061 (vr_mapping_logic) is a duplicate of T016b. T016b is in Phase 3. T061 is in Phase 3. This creates redundancy and potential conflict in the ordering.
- T023 (bayesian execution) depends on T051 and T022. T051 is complete. T022 is incomplete. T023 is incomplete. Ordering is valid but blocked.
- T026 (parameter recovery) depends on T022 and T023. T022 and T023 are incomplete. T026 is incomplete. Ordering is valid but blocked.
- T024 (model comparison) depends on T022 and T023. T022 and T023 are incomplete. T024 is incomplete. Ordering is valid but blocked.
- T025 (PPC) depends on T022 and T023. T022 and T023 are incomplete. T025 is incomplete. Ordering is valid but blocked.
- T027a (ΔAIC calculation) depends on T024. T024 is incomplete. T027a is incomplete. Ordering is valid but blocked.
- T027b (ΔAIC threshold) depends on T027a. T027a is incomplete. T027b is incomplete. Ordering is valid but blocked.
- T027b-test (unit test) depends on T027b. T027b is incomplete. T027b-test is incomplete. Ordering is valid but blocked.
- T030 (regression) depends on T022 and T023 (model execution). T022 and T023 are incomplete. T030 is incomplete. Ordering is valid but blocked.
- T031 (Bonferroni) depends on T030. T030 is incomplete. T031 is incomplete. Ordering is valid but blocked.
- T032 (sensitivity analysis) depends on T030. T030 is incomplete. T032 is incomplete. Ordering is valid but blocked.
- T033 (report generation) depends on T030, T031, T032. All are incomplete. T033 is incomplete. Ordering is valid but blocked.
- T034 (report logic) depends on T033. T033 is incomplete. T034 is incomplete. Ordering is valid but blocked.
- T054b (fetch_real) depends on T050 (interface). T050 is complete. T054b is marked [X] (complete). Ordering is valid.
- T041 (parse_real_logs) depends on T054b. T054b is complete. T041 is marked [X] (complete). Ordering is valid.
- T042 (end-to-end real) depends on T054b, T041, T016. T054b and T041 are complete. T016 is incomplete (depends on T044). T042 is incomplete. Ordering is valid but blocked by T016.
- T054c (verify VR mapping) depends on T016 and T041. T041 is complete. T016 is incomplete. T054c is incomplete. Ordering is valid but blocked.
- T054d (end-to-end real test) depends on T054b, T041, T016. T054b and T041 are complete. T016 is incomplete. T054d is incomplete. Ordering is valid but blocked.
- T039 (edge case tests) depends on T013, T022, T016. T013, T022, T016 are incomplete. T039 is incomplete. Ordering is valid but blocked.
- T040 (quickstart validation) depends on T006, T018, T056. T006 is complete. T018 and T056 are incomplete. T040 is marked [X] (complete). This is a contradiction: T040 claims to be complete but depends on incomplete tasks. This is a semantic ordering violation.
- T060 (streaming_loader) is listed in Phase N as well as Phase 3. This is a duplicate entry. The Phase N entry depends on T054b (complete). The Phase 3 entry depends on T054b (complete). This is redundant and confusing.
- T045 (MDES) and T046 (validation) are marked as blocking for Phase 3 but are incomplete. The text states 'T045 and T046 are the BLOCKING TASKS for Phase 3'. Since they are incomplete, Phase 3 cannot start. This is a valid ordering constraint, but the tasks themselves are not executable due to missing inputs (N=200, SD=1.0 are defined in plan.md, but the task requires T005 which is complete). The issue is that T045 is not marked complete, blocking the entire pipeline.
- T044 (unity_blend_shapes.yaml) is incomplete. T016 and T038 depend on it. This blocks the salience mapping path. The ordering is correct (config before usage), but the task is not done.
- T055 (schema_equivalence) is incomplete. It depends on T050 and T008b (both complete). The task is not done, but the ordering is valid.
- T015 (ingest.py) depends on T013 and T014 (simulation). This is a semantic violation: the real data ingestion should not depend on simulation tasks. It should depend on T054b and T041.
- T060 (streaming_loader) is in Phase 3 but depends on T054b (Phase 6). This is a forward dependency violation.
- T061 (vr_mapping_logic) is a duplicate of T016b. This creates ambiguity in the ordering.
- T042 (end-to-end real) depends on T016 (Phase 3). T016 is incomplete. This blocks the real data path. The ordering is valid but the dependency is not met.
- T054c (verify VR mapping) depends on T016 (Phase 3). T016 is incomplete. This blocks the verification step.
- T054d (end-to-end real test) depends on T016 (Phase 3). T016 is incomplete. This blocks the test.
- T040 (quickstart validation) is marked complete but depends on T018 and T056 which are incomplete. This is a semantic violation: a task cannot be complete if its dependencies are not.
- T060 is duplicated in Phase 3 and Phase N. This is a redundancy issue.
- T045 and T046 are incomplete, blocking Phase 3. The ordering is correct, but the tasks are not executable.
- T044 is incomplete, blocking T016 and T038. The ordering is correct, but the task is not done.
- T015 depends on T013 and T014 (simulation) instead of T054b and T041 (real). This is a semantic ordering violation.
- T060 depends on T054b (Phase 6) but is in Phase 3. This is a forward dependency violation.
- T061 is a duplicate of T016b. This creates ambiguity.
- T042, T054c, T054d depend on T016 (Phase 3) which is incomplete. This blocks the real data path.
- T040 is marked complete but depends on incomplete tasks. This is a semantic violation.
- T060 is duplicated.
- Task T016 requires mapping stories to VR scenes using 'data/config/unity_blend_shapes.yaml' (T044). However, T044 is marked as incomplete (no [X]) and the task description does not specify the exact schema or keys expected in that YAML file. An implementer cannot write the mapping logic without knowing the expected input structure.
- Task T060 appears twice in the document (once in Phase 3, once in Phase N) with identical descriptions. This duplication creates confusion about the task's phase and priority. One instance must be removed.
- T042 implements an 'End-to-End Real Data Pipeline' and asserts it must run when `DATA_MODE='real'`. Plan.md 'Summary' explicitly states the current phase is 'Simulation Only' and real data integration is 'Deferred' to Phase 4. Implementing and testing the real-data path in Phase 6 (which is part of the current tasks list) contradicts the Plan's scope definition. While the capability is needed eventually, including it as an active task in the current 'Validation' phase list without a clear 'Deferred' marker or separate phase boundary violates the Plan's explicit staging of work.
