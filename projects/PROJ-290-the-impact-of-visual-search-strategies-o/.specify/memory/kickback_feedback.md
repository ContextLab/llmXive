# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): No code, script, or documentation implementing the Generic ROI Fallback (3x3 grid) logic is present; the artifact is missing entirely, so the requirement is not satisfied. The next implementer must add the fallback implementation and provide the corresponding source file or test evidence.
- `T014` (rejected 1x): The submission provides no code, script, or documentation showing a participant‑exclusion routine that drops participants with >20 % missing gaze data, nor any log output reporting the exclusion rate. Without these artifacts the requirement cannot be verified.
- `T015` (rejected 1x): The submission provides no visible `data/raw/` directory nor any checksum files documenting downloaded datasets; no artifacts were presented to verify that the required structure and checksum records exist. The task therefore remains unfulfilled.
- `T037a` (rejected 1x): No evidence was provided that `hash_artifacts.py` was executed, nor that a `state/` directory containing updated hash files exists; the required artifact (the updated hashes) is missing.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/features.csv
- `T020` (rejected 1x): The repository contains `code/features/classification.py` with a `calculate_continuous_ratio` function that computes the ratio and logs a warning, but it never writes the updated DataFrame back to `data/processed/features.csv`. Moreover, the required `data/processed/features.csv` file is absent from the project. Both the output artifact and the persistence step are missing, so the task is not fully satisfied.
- `T024b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/labels_k2.csv, data/processed/labels_k3.csv
- `T025` (rejected 1x): declared artifact(s) missing/empty/invalid: results/sensitivity_report.yaml
- `T026` (rejected 1x): declared artifact(s) missing/empty/invalid: results/sensitivity_report.yaml
- `T038` (rejected 1x): declared artifact(s) missing/empty/invalid: results/report.md

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

