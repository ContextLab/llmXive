# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required `projects/PROJ-884-llmxive-follow-up-extending-self-improvi/...` directory tree is provided; without a listing or screenshot confirming the folders were created, we cannot confirm the task was actually performed. The implementer must supply proof (e.g., a directory tree dump) that the specified structure exists.
- `T001b` (rejected 1x): No repository initialization or `.gitignore` file is presented in the provided evidence; the claim lacks any tangible artifact confirming that a git repo was created and a basic Python‑oriented `.gitignore` was added.
- `T002a` (rejected 1x): No evidence of a Python 3.11 virtual environment (e.g., a `venv/` folder with activation scripts, `pyproject.toml`, or `requirements.txt`) exists in the specified `projects/PROJ-884-llmxive-follow-up-extending-self-improvi/` path. The task’s core deliverable is missing.
- `T003` (rejected 1x): The implementer supplied only a high‑level feature specification for dataset verification and evolutionary search; there is no evidence of any linting or formatting configuration (e.g., a `pyproject.toml`, `.flake8`, or `black` settings file) nor any scripts invoking flake8/black. Consequently, the required artifact for task T003 is missing.
- `T004` (rejected 1x): No evidence of the required `data/raw/` and `data/processed/` directories is provided; the claim lacks any tangible artifact showing the directory structure was created. The task remains undone.
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

