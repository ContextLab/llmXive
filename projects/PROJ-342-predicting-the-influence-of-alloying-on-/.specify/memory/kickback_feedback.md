# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The `code/ingest.py` file is incomplete: it never checks for existing files or checksum mismatches, does not log a `FALLBACK_USED` warning, lacks chunked reading logic, does not verify row count, does not write `source_doi` into `data/ingestion_stats.json`, and does not emit `DataInsufficientWarning`/`DataInsufficientError`. Moreover, the required raw CSV files are missing and `ingestion_stats.json` lacks the `source_doi` key. These omissions mean the task requirements are not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

