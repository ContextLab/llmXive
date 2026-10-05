# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/` directory or its `code/`, `data/`, `tests/` subfolders (and their subfolders from `plan.md`) was provided. The implementer did not supply any filesystem artifact confirming the project structure was created.
- `T001b` (rejected 1x): declared artifact(s) missing/empty/invalid: projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/requirements.txt
- `T001c` (rejected 1x): No .gitignore file content or confirmation of its existence at `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/.gitignore` is provided; thus the required artifact is missing.
- `T002a` (rejected 1x): No virtual environment directory or any files were presented at the specified path, so the required artifact does not exist. The task’s core requirement—creating a Python venv in `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/venv/`—is unmet.
- `T002b` (rejected 1x): The required `requirements.txt` file at the specified path is missing, so no dependencies could be installed into the virtual environment. Without this artifact the task cannot be considered fulfilled.
- `T002c` (rejected 1x): No evidence (e.g., screenshots, command output, or logs) showing that a virtual environment was activated and that `python --version` and `pip list` were run and verified is provided. The required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

