# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The provided `preprocess.py` only shows configuration loading and schema validation; there is no implementation of the left‑censored moving‑average calculation or the exclusion of the period immediately before the event window. Additionally, the required root‑level `config.yaml` is missing, so the verification step cannot compare values as specified. The task’s core logic is not present.
- `T017` (rejected 1x): The required output `data/processed/master_dataset.csv` and its SHA‑256 checksum file are absent, and the referenced schema files (`contracts/earthquake.schema.yaml`, `contracts/pressure-anomaly.schema.yaml`) are missing, so the verification steps cannot be performed. The task therefore has not been fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

