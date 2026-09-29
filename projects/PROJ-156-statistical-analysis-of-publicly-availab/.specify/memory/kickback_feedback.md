# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013b` (rejected 1x): The repository lacks a `config.yaml` file, so the required project‑specific salt cannot be read, and the provided `preprocess.py` excerpt does not show any function that hashes `runner_id` with SHA‑256 and the salt. Consequently the runner‑ID anonymization task is not fulfilled.
- `T015` (rejected 1x): No evidence of modified `fetch_data.py` or `preprocess.py` implementing a checkpoint mechanism is provided; the required code artifacts are missing, so the task’s requirement cannot be confirmed as satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

