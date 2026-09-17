# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007b` (rejected 1x): No `mode_selector.py` file or code snippet defining the required logic is provided; the evidence contains only the task description without any implementation artifact, so the required definition cannot be verified. The missing implementation must be added to satisfy the task.
- `T008` (rejected 1x): No `validation_utils.py` file is present in the provided evidence, nor any code snippet showing checksum verification or file‑integrity functions. The required artifact is missing, so the task is not satisfied.
- `T009` (rejected 1x): No logging configuration file, code snippet, or documentation was presented that sets up logging to both `logs/analysis.log` and standard output. The required artifact is missing, so the task is not satisfied.
- `T010` (rejected 1x): No code, configuration file, or test evidence was provided that demonstrates loading `cutoff_radius` and `zenodo_url` from environment variables. The required artifact (e.g., a module or script implementing this configuration management) is missing, so the task is not satisfied.
- `T014` (rejected 1x): No `download.py` script or any code implementing the required download-and-checksum functionality is present in the provided evidence. The task explicitly demands a concrete implementation that can retrieve trajectories from Zenodo or HuggingFace and verify their integrity, which is missing.
- `T016` (rejected 1x): No code, test, or log artifacts were provided showing that validation logic for detecting disconnected graph components was added or that warnings are logged as required by US‑1 Scenario 3. The implementer’s claim cannot be verified without concrete implementation evidence.
- `T027` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/descriptors.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

