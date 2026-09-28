# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The repository lacks the required `contracts/dataset.schema.yaml` file, and the `validate_schema` function in `code/ingestion.py` is truncated, providing no evidence that it checks for missing columns or exits with the exact “FATAL: Dataset Mismatch” message. Both the schema file and a complete verification implementation are needed.
- `T013` (rejected 1x): No code, script, or log file implementing the subject‑validation logic is provided; the claim lacks any artifact showing how fMRI and MWQ data are joined, how unmatched pairs are excluded, or how counts are logged. The required implementation and its output are missing.
- `T014` (rejected 1x): No code, script, log file, or filtered dataset was provided to demonstrate that per‑subject mean FD > 0.5 mm subjects are excluded, that exclusion counts and IDs are logged, and that a filtered dataset is output. The required artifacts are missing.
- `T015` (rejected 1x): No code, script, log file, or test output showing a zero‑variance check, warning, or logged exclusion count is provided; without such artifacts we cannot confirm the requirement was implemented. The implementer must supply the updated ingestion/processing code (or a diff) and example logs demonstrating the exclusion count.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

