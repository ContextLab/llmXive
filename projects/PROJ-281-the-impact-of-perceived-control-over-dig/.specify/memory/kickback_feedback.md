# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014b` (rejected 1x): The provided `code/services/anxiety_scoring.py` contains only entropy‑based text quality filtering and does not implement language detection with `langdetect` nor the specified confidence‑threshold logic. Moreover, the required configuration file `contracts/analysis.schema.yaml` and the raw data file `data/raw/social_media.csv` are missing, so the code cannot read the needed settings or data. The task’s core requirements are therefore not met.
- `T014c` (rejected 1x): The `anxiety_scoring.py` file is present but the implementation is truncated and does not clearly show full filtering logic or proper raising of `ConfigurationError` with specific key names. Moreover, the required input file `data/processed/preprocessed_text.csv` and the configuration file `contracts/analysis.schema.yaml` are missing, so the code cannot be exercised as specified. The missing files and incomplete code must be provided to satisfy the task.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

