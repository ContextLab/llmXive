# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T048` (rejected 1x): The repository contains a `loader.py` with checksum utilities, but it never invokes verification for `data/processed/subtle_cue_subset.parquet`, does not write results to `data/processed/integrity_log.txt`, and the required parquet file and log file are absent. Consequently the task’s three mandatory requirements are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

