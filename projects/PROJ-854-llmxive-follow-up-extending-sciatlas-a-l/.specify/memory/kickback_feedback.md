# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): The implementer provided only a claim placeholder and no actual artifacts (no code, dataset, computed metrics, or analysis results). Required outputs such as a data ingestion pipeline, per‑node `bridging_coefficient` and `primary_cluster` values, citation counts, novelty scores, and the correlation/regression analysis are missing.
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: conftest.py
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/subgraph_with_clusters.parquet

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

