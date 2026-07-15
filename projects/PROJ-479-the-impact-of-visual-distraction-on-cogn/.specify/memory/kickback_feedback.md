# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): The implementer provided only a feature specification and no evidence of a `code/` directory existing at the repository root; the required artifact is missing.
- `T001b` (rejected 1x): No `data/` directory is present in the repository root; the provided artifacts consist only of a feature specification and no filesystem changes. The required directory creation is missing.
- `T001c` (rejected 1x): No evidence was provided that a `results/` directory exists at the repository root; without a directory listing or a file path confirming its creation, the requirement cannot be verified as satisfied.
- `T001d` (rejected 1x): No evidence of a `tests/` directory at the repository root is provided; the only artifacts shown are feature specifications and user stories, with no file listings or directory structure confirming the required folder exists. The task’s sole requirement—creating the `tests/` directory—is therefore unmet.
- `T001e` (rejected 1x): No evidence of a `specs/001-visual-distraction-cognitive-control/` directory (or any files within it) is provided; the implementer did not supply a directory listing or any artifacts confirming the required structure exists. The task remains undone until the directory is created and shown.
- `T003` (rejected 1x): The provided evidence contains only a research feature specification and no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings). Consequently, the requirement to configure ruff/flake8 and black is not met. Adding the appropriate configuration artifacts is needed to complete the task.
- `T010` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/unit/test_synthetic_data.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

