# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence was provided that the required directories (`code/`, `data/`, `contracts/`, `tests/`) actually exist or contain any files; the response contains only the task description and specifications, not the claimed project structure. The implementer must create and show these directories (with at least placeholder files) to satisfy the requirement.
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T019` (rejected 1x): The `contracts/output.schema.yaml` file required for validating the CSV structure is missing, and the `code/main.py` implementation is truncated before completing the aggregation and CSV‑writing logic, so the batch processing functionality is not fully present. The next implementer must add the missing schema file and ensure `aggregate_metrics_to_csv` correctly writes the two CSVs according to that schema.
- `T028` (rejected 1x): No code, test, or documentation artifact was provided showing that the pipeline now checks for zero significant findings after FDR correction and adds an explicit statement to the report. The required implementation and verification evidence are missing.
- `T035` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T040` (rejected 1x): No evidence of updated files in `docs/` or modifications to `README.md` was provided; the claim lacks any actual documentation artifacts to verify.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

