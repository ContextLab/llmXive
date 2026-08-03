# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): No environment configuration files (e.g., `requirements.txt`, `environment.yml`, Dockerfile, or similar) or code that sets and documents a random seed for reproducibility are present. Consequently, the task of setting up reproducible environment and seed management is not demonstrated.
- `T015` (rejected 1x): No code, script, or documentation implementing the ROI mapping logic is present; the provided project excerpt only describes higher‑level user stories and testing criteria, but there is no artifact that actually assigns gaze points to the “source attribution” or other bounding boxes. The required implementation artifact is missing.
- `T016` (rejected 1x): No code, script, log file, or any other artifact demonstrating that trials with missing ROI coordinates are excluded and that exclusion counts are logged was provided. Without such evidence, we cannot confirm the edge‑case handling was implemented. The implementer must supply the preprocessing script (or relevant module) and example output/log showing the exclusions.
- `T023` (rejected 1x): The provided `code/04_data_merge.py` is truncated (ends mid‑function) and does not contain the merging logic required by the task. Moreover, the three input CSV files (`preprocessed_gaze.csv`, `empirical_outcomes.csv`, `valence_scores.csv`) are absent from the repository, so the script cannot be exercised or verified. The implementation must be completed and the required data files supplied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

