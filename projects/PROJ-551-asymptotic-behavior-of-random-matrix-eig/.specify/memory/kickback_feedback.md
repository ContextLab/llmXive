# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The results JSON, log, raw matrix, and quickstart command all exist and the run demonstrably executed (identical top eigenvalue 2.901642355090901 across the main run and the repro_check_1.json re-run, satisfying the 1e-6 reproducibility criterion in substance). However, verification requirement (a) cannot be met: `simulation_run.schema.yaml` and `eigenvalue_result.schema.yaml` are MISSING from the project, so the JSON was never validated against the contracts. Additionally, the recorded test run `tests/test_t001.py` FAILED (exit 1) — the reproducibility test invoked `--k data/processed/repro_c

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

