# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013b` (rejected 1x): The repository contains a partially‑implemented `code/ingest.py`, but the script does not include a complete function that fetches the Kp index data and writes it to `data/raw/kp_indices.csv`, and the expected CSV file is absent from the project. Consequently the required artifact and its validation are missing.
- `T016` (rejected 1x): No `aligned_events.csv` (or any derived file) containing the required `is_recurrent` flag was provided. The evidence lacks the primary dataset with the recurrent‑activity flag, so the task’s core requirement is not demonstrated.
- `T018` (rejected 1x): The repository lacks the required `contracts/aligned_event.schema.yaml` (the schema file is missing), so `code/validate.py` cannot actually validate the CSV. Moreover, the provided `validate.py` only defines validation functions and does not contain any logic that prevents writing `aligned_events.csv` or updating `data/source_manifest.yaml` when validation fails. Both the essential schema and the blocking behavior are absent.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

