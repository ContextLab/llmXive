# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`data/raw`, `data/processed`, `code`, `tests`, `code/contracts`) being created is provided; the implementer did not supply any artifact showing the project structure exists. The task is therefore not satisfied.
- `T005` (rejected 1x): The required artifact `contracts/config.schema.yaml` does not exist in the repository, so the schema validation step cannot be performed. Without this file the implementation in `code/main.py` cannot fully satisfy the task’s requirement to create and use the schema.
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T012a` (rejected 1x): The required `data/raw/fluview_ili.csv` file is absent, and the provided `code/download_data.py` is truncated (ends mid‑function) with no visible logic that actually downloads the CSV, saves it to the specified path, or verifies a checksum. Consequently the task’s core requirement is not met.
- `T012b` (rejected 1x): The repository lacks the required `data/raw/ground_truth_events.csv` file, and the provided `code/download_data.py` is truncated before any logic that fetches ground‑truth data and writes the CSV with the columns `start_week, end_week, event_name`. Consequently the implementation does not meet the task’s specifications.
- `T016` (rejected 1x): The required `data/raw/ground_truth_events.csv` file is absent, so the script cannot actually load and validate real ground‑truth data. Moreover, the provided `code/evaluate.py` is truncated and does not contain any logic for parsing the ±2‑week tolerance window required by FR‑006. Both the essential data artifact and the full implementation are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

