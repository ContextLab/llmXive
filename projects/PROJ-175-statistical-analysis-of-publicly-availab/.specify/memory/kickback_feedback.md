# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/pilot_stats.json
- `T013a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/recipe1m_processed.parquet
- `T014` (rejected 1x): The submission contains only the task description and specification; no actual pipeline code, no normalized ingredient CSV, and no generated co‑occurrence matrix or similarity scores are provided. The required artifact—a validated CSV file (or equivalent) produced by the preprocessing pipeline—is missing, so the task is not satisfied.
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/co_occurrence_matrix.parquet

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

