# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): The `code/02_feature_engineering.py` script and the output CSV `data/raw/descriptors_added.csv` exist and contain the required descriptor and fingerprint columns, but the accompanying unit test `code/tests/test_feature_engineering.py` fails to import the module (FileNotFoundError) and therefore does not verify the descriptor values as required. The broken test means the task’s verification step is not satisfied. Fix the test’s import path (or adjust the project layout) so the test can run and confirm the computed descriptors.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

