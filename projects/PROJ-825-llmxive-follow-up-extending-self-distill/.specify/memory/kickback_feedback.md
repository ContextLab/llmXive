# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007` (rejected 1x): The logger and test files exist and the historical pytest run passed, but the required contract `training_run.schema.yaml` is MISSING from the project — the test's schema validation step (`SCHEMA_PATH = .../contracts/training_run.schema.yaml`) would fail on a fresh run, and the task's verification criterion explicitly requires round-trip validation against that schema. The implementer must add the schema (with fields matching what the logger emits: variant, env, seed, step, reward, cpu_time_sec, peak_memory_mb, run_id, timestamp) so the test passes against a real, present contract.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

