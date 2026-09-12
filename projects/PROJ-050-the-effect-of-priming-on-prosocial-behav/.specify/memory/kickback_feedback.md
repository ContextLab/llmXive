# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011` (rejected 1x): The required file `tests/unit/test_classification.py` does not exist, so no unit test for the negation‑aware keyword classification logic is present. The task’s deliverable is missing entirely.
- `T012` (rejected 1x): The required artifact `tests/unit/test_anonymization.py` does not exist on disk, so no unit test for PII anonymization is provided. The task cannot be considered completed until the file is created with appropriate tests.
- `T015b` (rejected 1x): No code, log output, or comment indicating that a CPU feasibility analysis for FR‑002c was performed (or that the feature was deferred) is present. The required artifact—a file containing the feasibility check logic or a comment/log entry “FR‑002c Deferred”—is missing.
- `T017` (rejected 1x): The required output files `data/processed/anonymized.csv` and `data/processed/raw_counts.json` are absent, and the provided `code/01_ingest.py` is truncated and does not contain logic that writes those files. Consequently the task’s core requirement—to save the processed CSV and JSON—is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

