# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The submission provides no visible `code/`, `tests/`, or `data/` directories or any files within them; therefore the required project structure is missing. The task cannot be considered fulfilled until those three top‑level folders are created and contain appropriate starter content.
- `T002` (rejected 1x): The implementer provided only a feature specification and no project initialization artifacts (e.g., `pyproject.toml`, `requirements.txt`, `environment.yml`, or a `setup.cfg` containing the listed dependencies). Consequently, there is no evidence that a Python 3.11 project with the required packages has been created. The missing initialization files must be added to satisfy the task.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) were supplied, nor any documentation showing they have been integrated into the project. The required artifact for task T003 is therefore missing.
- `T004a` (rejected 1x): The required file `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` does not exist, so no predictor schema has been defined. The task’s core artifact is missing, making the implementation incomplete.
- `T004b` (rejected 1x): The required file `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` does not exist, so no outcome schema for sleep metrics has been defined. The task’s primary artifact is missing, making the implementation incomplete.
- `T005a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: github/workflows/analysis.yml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

