# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The repository lacks the required `config.yaml` file, so thresholds cannot be loaded, and the provided `generate_data.py` snippet does not show any concrete labeling logic that uses those thresholds. Without the configuration file (and evidence of the labeling implementation), the task is not genuinely fulfilled.
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/synthetic_episodes.parquet, data/checksums.json
- `T016c` (rejected 1x): The required output files `data/processed/train.parquet` and `data/processed/test.parquet` are not present, indicating that the geometry‑disjoint split was not actually performed and saved. Consequently the task’s core requirement is unmet.
- `T018` (rejected 1x): The repository lacks a `config.yaml` file, so custom thresholds cannot be read, and the provided `generate_data.py` excerpt does not show any new function that re‑labels the raw `synthetic_episodes.parquet` and re‑runs the geometry‑disjoint split logic as required. Both the necessary configuration source and the specific re‑labeling/split function are missing.
- `T025` (rejected 1x): The implementer did not provide any model summary output or any file showing the total parameter count. No artifact demonstrating that the model has fewer than 10,000,000 parameters before saving is present, so the task requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

