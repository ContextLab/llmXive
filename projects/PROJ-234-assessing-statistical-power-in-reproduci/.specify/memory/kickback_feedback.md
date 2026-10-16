# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The required root directory `projects/PROJ-001-assessing-statistical-power/` is missing; the scaffolded directories (`code/`, `data/`, `tests/`, `docs/`, `contracts/`) exist at the repository root instead of under the specified project path, so the task’s directory‑tree requirement is not satisfied.
- `T004` (rejected 1x): Checked the unit‑test logs for the three required utilities. `test_parsers.py` and `test_oa_checker.py` both passed, but `test_api_client.py` failed: the test expecting a `DataFetchError` on a bad URL did not raise the exception (see `code/.tasks/T004.tests_unit_test_api_client.py.log`). Consequently the `api_client.py` does not meet the specification (no proper error handling/exponential‑backoff), so the task is not fully satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

