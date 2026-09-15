# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005` (rejected 1x): The repository contains a partially shown `code/data/synthetic.py`, but the implementation is truncated and does not demonstrate writing the required CSV and JSON files, nor does it include the CLI (`--generate --validate-schema`) or schema validation against `contracts/dataset.schema.yaml`. Moreover, the expected output files `data/processed/synthetic_mar_v1.csv`, `data/processed/synthetic_mar_v1_meta.json`, and the schema file are absent. The task’s core deliverables are therefore missing.
- `T005b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/synthetic_mar_v1.csv, data/processed/synthetic_mar_v1_meta.json, state/manifest.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

