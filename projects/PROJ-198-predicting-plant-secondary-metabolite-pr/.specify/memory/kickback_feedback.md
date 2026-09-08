# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The claim provides no visible evidence of the required directories (`code/`, `data/raw`, `data/processed`, `tests/`) or any files within them; no directory listing or file contents were supplied. Without concrete artifacts, we cannot confirm that the project structure was actually created.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., pyproject.toml, .ruff.toml, .flake8, or black settings) are present in the provided evidence, so the requirement to configure ruff/flake8 and black has not been satisfied.
- `T004` (rejected 1x): No files or code defining Pydantic models for `Species`, `BGCFeature`, `Metabolite`, or `ModelOutput` were presented in `code/models/`; the evidence does not show any such artifacts exist or contain the required definitions. The implementer must add the model files with proper Pydantic classes.
- `T008` (rejected 1x): No code, configuration files, or documentation were provided showing that environment variables for API keys or local data paths have been created, managed, or documented. The claim lacks any tangible artifact to verify the setup.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

