# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The required directories and `data/dir_structure.txt` with the nine entries are present, but the CI verification step failed (see `code/.tasks/T001.tests_integration_test_dir_structure.py.log` with exit 1), so there is no evidence that the manifest was successfully checked by CI as required. The CI test must run and pass, confirming the file’s contents.
- `T007` (rejected 1x): The `code/simulation/generator.py` file does import and call `raise_if_unphysical` and `check_noise_level`, and the execution log shows the unphysical‑trajectory guard being triggered. However, there is no evidence that the required unit tests (the same ones as T006) were run and passed, nor any demonstration that `check_noise_level` emits a warning when the noise exceeds its threshold. Provide the unit‑test run output confirming all tests succeed and a case where `check_noise_level` raises the `HighNoiseWarning`.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

