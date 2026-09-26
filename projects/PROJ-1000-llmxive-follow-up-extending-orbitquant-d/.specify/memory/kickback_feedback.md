# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The submission provides no visible `code/`, `data/`, or `tests/` directories or any files within them, so the required project structure cannot be confirmed as created. The implementer must add these top‑level folders (with at least placeholder files) to satisfy the task.
- `T002` (rejected 1x): The evidence contains only a feature specification and user stories; there is no Python project scaffold, no `requirements.txt`/`pyproject.toml` or any code initializing the project with the listed dependencies. Consequently, the required artifact (a initialized project with the specified packages) is missing.
- `T003` (rejected 1x): No linting (ruff) or formatting (black) configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or CI scripts) were presented, nor any evidence that these tools have been set up in the repository. Without such artifacts, the requirement to configure linting and formatting is not satisfied.
- `T006` (rejected 1x): The repository contains a partially‑implemented `code/data/preprocess.py` (the file is truncated and never writes any CSV output). Moreover, the required output file `data/processed/prompts.csv` is missing entirely. Consequently the task of extracting captions and creating the processed CSV split is not fulfilled.
- `T022` (rejected 1x): The repository contains a `code/analysis/clustering.py` file, but its content is truncated and does not show a complete implementation of the required clustering pipeline and generation of the rotation matrices. Moreover, the required output file `data/processed/clustering_report.json` is absent. Both the artifact and the expected JSON report are missing, so the task is not satisfied.
- `T023a` (rejected 1x): The required `data/processed/clustering_report.json` file is absent, so the validator cannot actually confirm its existence or contents. Moreover, the provided `validate_clustering.py` is truncated and contains no top‑level code that loads the file, checks for its presence, or invokes the validation functions, meaning the implementation does not fully satisfy the task.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

