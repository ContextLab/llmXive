# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listing, path confirmation, or any file‑system artifact showing `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/` was provided; therefore we cannot verify that the required project root directory was actually created.
- `T002` (rejected 1x): The submission contains only the task description and feature specification; there is no evidence (e.g., a directory tree, screenshots, or file listings) showing that the required `code/` subdirectories actually exist. Without concrete proof of those folders being created, the task requirement is not satisfied.
- `T003` (rejected 1x): No evidence was provided that the required directories `data/raw/`, `data/processed/`, and `data/models/` actually exist in the repository; the “Actual artifacts / evidence on disk” section is empty. The implementer must create these subdirectories (and optionally show their presence, e.g., via a directory listing).
- `T004` (rejected 1x): No evidence was presented that the `state/` and `docs/` directories actually exist in the repository; the response only contains a feature specification and does not show any created folder structure or files within them. The implementer must add the required directories (and optionally placeholder files) to satisfy the task.
- `T005` (rejected 1x): No evidence of a `projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/` directory (or any files within it) is presented; the implementer did not supply the required directory structure.
- `T005c` (rejected 1x): No linting or formatting configuration artifacts (e.g., ruff/black settings in pyproject.toml, .ruff.toml, .pre-commit-config.yaml, or related scripts) are present; the only evidence relates to data extraction and model training, not to configuring ruff and black. The required linting setup is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

