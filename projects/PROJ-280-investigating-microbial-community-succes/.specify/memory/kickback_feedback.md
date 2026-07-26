# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T03a` (rejected 1x): No `.flake8` file was presented in the evidence; the required configuration file at `projects/PROJ-280-investigating-microbial-community-succes/.flake8` with the specified rules is missing. The implementer must add the file containing `max-line-length = 100`, `ignore = E203,W503`, and `exclude = venv,build`.
- `T004` (rejected 1x): The `code/validators.py` script is present and implements `validate_dataset_config` as specified, but the required schema file `contracts/dataset-config.schema.yaml` is missing entirely, so the validation cannot run and the task’s core deliverable is absent. The missing schema must be added with the exact YAML definition.
- `T014` (rejected 1x): The required output files `data/processed/low_depth_results.json`, `data/processed/medium_depth_results.json`, `data/processed/high_depth_results.json`, and the final `data/processed/robustness_verification_report.json` are not present on disk, indicating the sensitivity‑analysis step was not actually executed or saved. The implementation in `code/02_preprocess.py` does not produce these artifacts.
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/diversity_metrics.json, schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

