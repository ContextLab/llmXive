# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007` (rejected 1x): The repository contains `code/data/download_nvd.py`, but the file is truncated and implements an API‑based fetch rather than downloading the official yearly JSON feeds, and it never creates the required `data/raw/nvd_cve_merged.json.gz` and its `.sha256` checksum (both files are missing). Consequently the task’s output artifacts are absent and the implementation does not follow the specified logic.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

