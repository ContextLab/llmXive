# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): No evidence of the required `projects/PROJ-357-the-impact-of-visual-crowding-on-facial-/` directory or its subfolders (`code/`, `data/`, `tests/`, `artifacts/`, `state/projects/`) is provided; the implementer did not supply any file or directory listings to confirm their creation. The task remains undone.
- `T015` (rejected 1x): No `data/interim/stimuli` image files or a `stimuli_manifest.json` file were presented, and there is no evidence that a validation script was run to check correspondence and exact parameter values. The required artifact (the manifest and its verification) is missing.
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/clutter_metrics.csv
- `T023` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/validation_report.json
- `T029` (rejected 1x): No code, script, notebook, or data file was provided that computes per‑trial accuracy and aggregates it by stimulus ID, emotion, and flanker count. Without such an artifact, the requirement cannot be verified. The next implementer must supply the implementation (e.g., a function or script) and a sample output showing the aggregated accuracy table.
- `T027` (rejected 1x): No evidence of `pilot_runner.py` being executed with `synthetic_data_generator.py` is provided—there are no generated raw synthetic response data files, logs, or output artifacts to confirm the pilot run was performed. The required synthetic response dataset is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

