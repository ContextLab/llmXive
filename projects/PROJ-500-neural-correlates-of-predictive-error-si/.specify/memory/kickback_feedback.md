# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005c` (rejected 1x): No repository directory, `.git` folder, or `.gitignore` file is present in the provided evidence; thus the required artifact for initializing a Git repository and configuring its ignore rules is missing.
- `T006` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml`, or a pre‑commit hook invoking ruff/black) are present in the provided artifact list, so the requirement to configure ruff and black is not satisfied. The implementer must add the appropriate configuration files and ensure they are non‑empty.
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T010` (rejected 1x): No artifact (e.g., configuration files, validation scripts, or documentation) was provided that defines environment variable validation or error‑handling infrastructure. Consequently the requirement to set up such infrastructure is not demonstrated.
- `T016` (rejected 1x): The repository lacks the required output files (`data/excluded_subjects.csv` and `data/validation_report.json`). Moreover, `src/data/preprocess.py` is truncated (the `write_excluded_subjects_csv` function is incomplete and no code updates the JSON report), so the artifact‑rejection and underpowered‑subject flagging logic is not fully implemented.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

