# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The required artifact `tests/integration/test_us1_pipeline.py` does not exist in the repository, so the integration test for the US1 pipeline on 2 subjects is missing. The task cannot be considered completed until this file is added with the appropriate test implementation.
- `T041a` (rejected 1x): No artifacts (e.g., formatted source files, a report, or command‑line output) are provided to demonstrate that `black` and `isort` have actually been run on the `code/` and `tests/` directories. Without such evidence the claim cannot be verified.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

