# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `task-format` (rejected 1x): Tasker must repair ambiguous task identities while preserving requirements. Malformed: ['- [ ] T018/T019/T020b Subject filtering (missing scans, missing scores, motion > 0.5\u202fmm FD in >\u202f20\u202f% volumes) with standardized exclusion logging.', '- [ ] T043/T051/T051b/T017/T017.1/T017.2 OLS regression (`creativity ~ excess_flexibility + age + sex + education + static_strength`), static‑only baseline, ΔR² computation and 4‑decimal formatting, `data/interim/results.csv` with `global_empirical_p_value` from the permutation test.']; duplicates: []

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

