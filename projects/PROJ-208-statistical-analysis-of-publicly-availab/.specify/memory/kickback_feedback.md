# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009a` (rejected 1x): The repository contains `code/data/loader_hf.py`, but the script never writes the fetched data to `data/raw/github_issues_raw_hf.parquet` nor does it perform full schema validation against `contracts/dataset.schema.yaml`. Moreover, the required output parquet file and the schema file are absent from the project. Consequently the task’s deliverables are not present.
- `T009b` (rejected 1x): The required output file `data/raw/github_issues_raw_api.parquet` does not exist, and the provided `loader_api.py` is truncated (no visible logic for fetching issues, handling stop conditions, or writing the Parquet file). Without the generated dataset, the task’s deliverable is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

