# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The provided evidence contains only a feature specification and user stories; there is no artifact showing that the required root directories under `projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/` have been created (or that they contain any files). The task’s core requirement—creating those directories—is not demonstrated.
- `T001b` (rejected 1x): No directory tree or file listings were provided to confirm that `src/`, `tests/`, `data/` and all the required sub‑directories (e.g., `data/raw`, `src/generation`, `tests/unit`, etc.) actually exist. Without concrete evidence of these folders being created, the task requirement is not satisfied. The implementer must supply a directory listing or screenshots showing the full hierarchy.
- `T002` (rejected 1x): The implementer only supplied a feature specification and user stories; there is no evidence of a Python project being created (e.g., a repository, `pyproject.toml`, `requirements.txt`, or any code initializing the listed packages). The required artifact—a initialized project with the specified CPU‑only dependencies—is missing.
- `T003` (rejected 1x): The provided evidence contains only high‑level feature specifications and user stories for a physics‑filter pipeline; there are no linting or formatting configuration files (e.g., `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections, `.ruff.toml`, or CI scripts) or any indication that ruff and black have been set up. Consequently, the requirement to configure linting (ruff) and formatting (black) tools is not met. The implementer must add the appropriate configuration files and demonstrate they are active (e.g., by showing a successful lint/format run or CI integration).
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/io_utils.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

