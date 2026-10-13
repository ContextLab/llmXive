# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `task-format` (rejected 1x): Tasker must repair ambiguous task identities while preserving requirements. Malformed: ['- [ ] T024–T028, T034b, T046–T050 Streaming ingestion, fail‑loudly fetch, dataset verification pipeline (`data/config/datasets.yaml`, `results/real_world_ingestion_log.csv`), real‑data integrity tests.', '- [ ] T065, T065b, T065c, T070 `CONFIG_MATRIX`, distribution factory, parameter mapper, dynamic config loading.', '- [ ] T060–T062, T028a, T028b, T028d Metrics tests, Clopper‑Pearson CI, simulation loop orchestration with checkpointing and fidelity enforcement.', '- [ ] T033–T039, T051, T052, T056, T056b, T059, T066 US4 real‑world ingestion, sampling, pipeline reuse (`results/real_world_results.csv`), comparison report.']; duplicates: []

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

