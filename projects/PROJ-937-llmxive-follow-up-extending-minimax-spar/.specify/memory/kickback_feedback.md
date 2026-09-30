# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T032a` (rejected 1x): No code, script, data file, or documented output implementing the false‑positive‑rate calculation for the sensitivity analysis (selection without target vs Dense Attention) was provided. The required artifact is missing, so the task’s core requirement is not satisfied.
- `T032b` (rejected 1x): declared artifact(s) missing/empty/invalid: results/benchmark_report.json
- `T031` (rejected 1x): declared artifact(s) missing/empty/invalid: results/benchmark_report.json
- `T033` (rejected 1x): The implementer did not provide a `quickstart.md` file or any documentation showing CPU‑only execution instructions; only a feature specification and test scenarios are present, which do not satisfy the documentation update requirement. The required markdown artifact is missing.
- `T035` (rejected 1x): No test run logs, result files, or any indication that a full `pytest` suite was executed on a CPU‑only runner and that all tests passed are present. The implementer provided no artifacts to verify the required pytest execution.
- `T036` (rejected 1x): The required artifact `results/benchmark_report.json` does not exist, so there is no content to check for the specified keys. Without the file, the verification cannot be performed. The implementer must create the JSON file with the listed metrics.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

