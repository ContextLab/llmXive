# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required `projects/PROJ-890-llmxive-follow-up-extending-orca-the-wor/` directory or any of its sub‑folders/files is provided; the claim lacks any artifact showing the project structure was created.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.flake8` file, or CI scripts invoking these tools) are present in the provided evidence, nor any documentation showing they have been set up. The required artifacts to satisfy task T003 are missing.
- `T008` (rejected 1x): The submission contains only the feature specification and user stories; there is no evidence of a `data/` directory with the required `raw/`, `processed/`, and `validation/` subfolders, nor any checksum verification scripts. The necessary filesystem artifacts and scripts are missing, so the task is not satisfied.
- `T010` (rejected 1x): The required file `tests/integration/test_latent_extraction.py` does not exist, so no integration test is provided to verify latent extraction on a sample clip. The task’s core artifact is missing.
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/latents.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

