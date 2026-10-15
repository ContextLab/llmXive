# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): The Parquet file and checksums.txt exist and the log shows a real streaming run from `codeparrot/github-code` writing 2000 rows, but there is no evidence of the required per-language breakdown: the log never reports counts per language (Python vs. Java), the visible Parquet content shows only repo names with no confirmed `language` column values, and the value of N (from Phase-0 power analysis) is never stated or verified. The task's core verification — "contains exactly N rows per language" — is unproven; the implementer should log/verify per-language row counts (e.g., a groupby on `language`

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

