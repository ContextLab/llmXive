# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): The provided `code/ingestion.py` contains placeholder functions and no logic that reads `contracts/dataset.schema.yaml` or aborts with “FATAL: Dataset Mismatch” when required columns are absent. Moreover, the required `contracts/dataset.schema.yaml` file is missing entirely. Both the implementation and the schema artifact are absent, so the task is not satisfied.
- `T013` (rejected 1x): No code, script, or log files implementing the subject‑validation logic are present; the evidence consists only of the task description and project spec. The required artifact—a piece of software that joins fMRI and MWQ data, excludes unmatched subjects, and records exclusion counts—is missing.
- `T014` (rejected 1x): No code, script, configuration, or log file was provided that implements the per‑subject mean FD > 0.5 mm exclusion or records the exclusion counts (FR‑008). Without such artifacts, the requirement cannot be verified as satisfied.
- `T015` (rejected 1x): No code, script, or test file was presented that adds a zero‑variance (`global_signal_sd == 0`) exclusion check and logs a warning. The provided project description and user stories do not contain the required implementation artifact, so the task is not satisfied.
- `T022` (rejected 1x): The provided materials contain only the project specification and user stories; there is no code, script, function, or output that computes the empirical p‑value as the proportion of null MAEs ≤ the observed MAE. Consequently, the required artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

