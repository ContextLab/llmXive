# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The provided material only contains a feature specification and user stories; there is no evidence that the required project directories (`code/`, `data/`, `tests/`, `docs/`) have been created or contain any files. The implementer did not supply the actual folder structure or any contents, so the task is not satisfied.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., .ruff.toml, .flake8, pyproject.toml with Black settings) are present, nor any documentation showing that ruff/flake8 and Black have been set up for the project. The implementer provided only the unrelated neuroscience feature specification, so the required linting/formatting setup is missing.
- `T004` (rejected 1x): No code, configuration file, or validation script was provided to demonstrate loading ADNI credentials from a `.env` file or checking for required keys. The required artifact is missing, so the task is not satisfied.
- `T005` (rejected 1x): No `logs/pipeline.log` file or any logging output was presented; the evidence consists only of the feature specification and user stories, with no concrete artifact demonstrating that machine‑readable logs have been created per FR‑011. The required logging infrastructure is therefore missing.
- `T007` (rejected 1x): No evidence of the required directories (`data/raw/`, `data/processed/`, `data/analysis/`, `outputs/`) or a `.gitignore` file with rules for large files is present in the provided artifacts. The implementer has not supplied any files or directory listings to confirm the structure was created.
- `T008` (rejected 1x): No code, scripts, or modules implementing CSV read/write helpers or checksum validation were supplied; the only evidence is a high‑level project description unrelated to the required utility functions. The required artifacts are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

