# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listing or file tree was provided, so we cannot verify that `projects/PROJ-906-llmxive-follow-up-extending-liveedit-tow/` and its required subfolders (`data/raw`, `data/flow`, `data/metrics`, `code`, `code/data`, `code/models`, `code/metrics`, `code/analysis`, `tests/contract`, `tests/unit`, `results`) actually exist. The implementer must supply concrete evidence (e.g., a printed tree or screenshots) showing the full project structure.
- `T003` (rejected 1x): The claim provides no visible configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or a `black` config) or any other artifact showing that ruff linting and black formatting have been set up. Without such files or documentation, the requirement to configure these tools is not satisfied. The next implementer should add the appropriate configuration files and ensure they are committed to the repository.
- `T007` (rejected 1x): No files or code snippets were provided showing schema validator implementations in `code/contracts/`, nor any evidence that validators for Dataset, Metrics, and Analysis outputs exist. The required artifacts are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

