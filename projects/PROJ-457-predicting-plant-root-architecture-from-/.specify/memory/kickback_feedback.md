# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `task-format` (rejected 1x): Tasker must repair ambiguous task identities while preserving requirements. Malformed: ['- [ ] T004/T006/T007/T008 `code/config.py`, logging setup, base data models (`RootPhenotypeRecord`, `SoilNutrientRecord`), `config.yaml.template`.', '- [ ] T014a/T015g State file `artifacts/state.json` initialized; ISRIC verified‑source check performed — no verified ISRIC source exists; deviation logged, `is_isric_verified: false`.', '- [ ] T010/T012/T021/T022/T031 Unit and integration tests for preprocessing, species‑stratified splits, model pipeline, and file‑size constraint.', '- [ ] T013/T013b/T014/T014d/T015c–T015m/T035a–T035c Data ingestion from the verified HuggingFace merged‑dataset sources (fail‑loudly, no synthetic fallback), ISRIC‑unavailable path, P/N availability check, AM‑001 amendment record (`artifacts/sc_amendments.json`), FR‑012 observational filtering, missing‑nutrient exclusion per AM‑001, species‑count filtering (n≥20), species counts and SC‑001/SC‑005 metrics in `artifacts/reports/metrics.json` and `artifacts/reports/success_criteria_status.json`, deviation logs.']; duplicates: []

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

