# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/setup_log.json
- `T016` (rejected 1x): No code, data file, or result showing computed cosine similarity between ingredient embeddings is present; the only provided material is a high‑level project specification, which does not constitute the required artifact for T016. The task therefore remains unfinished.
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/functional_roles.parquet

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

