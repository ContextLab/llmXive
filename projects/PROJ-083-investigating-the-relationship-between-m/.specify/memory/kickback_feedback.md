# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of a `projects/PROJ-083-investigating-the-relationship-between-m/` directory (or any files within it) was provided; the claim lacks the required project‑structure artifact, so the task is not satisfied.
- `T003` (rejected 1x): The claim provides no linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.ruff.toml`, or CI steps invoking them). No artifacts exist on disk to demonstrate that ruff and black have been set up, so the requirement is not satisfied. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly reference ruff and black.
- `T004` (rejected 1x): No evidence of the required directories (`data/raw/`, `data/processed/`, `data/models/`, `code/`, `tests/`) is provided; the only artifact shown is a feature specification, not the actual folder structure. The task remains undone until the specified directory hierarchy exists in the repository.
- `T007` (rejected 1x): No schema files were presented; there is no evidence that `contracts/ReactionRecord` or `contracts/TopologicalDescriptor` definitions exist, are non‑empty, or contain the required fields. The implementer must add the two schema definition files in the `contracts/` directory.
- `T014` (rejected 1x): No code, script, or log file was provided that shows the implementation of a check for the number of EAS reactions (N_EAS) and the required critical‑error logging and halting behavior when N_EAS < 100. Without such an artifact, we cannot confirm the task’s requirement has been met. The missing artifact is the implementation (e.g., Python module, shell script, or pipeline step) that performs the count, logs a critical error, and aborts the pipeline with status “Insufficient Data”.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

