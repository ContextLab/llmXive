# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The repository contains a `tests/integration/test_baseline_generation.py` file, but it is truncated, calls a function (`generate_baseline_failures`) instead of executing the required `generate_baseline.py` script, and the expected output `data/raw/baseline_failures.json` does not exist. Consequently the integration test does not meet the stated constraint and cannot verify the real generation step.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

