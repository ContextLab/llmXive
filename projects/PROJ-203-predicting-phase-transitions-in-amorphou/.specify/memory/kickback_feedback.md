# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or corresponding CI scripts) are present in the provided evidence, so the required setup in the `code/` directory is missing. The implementer must add the actual configuration files and ensure they are non‑empty and correctly enable Ruff/Flake8 and Black for the project.
- `T006` (rejected 1x): No files or code snippets for `Composition`, `StructuralDescriptor`, or `ThermalProperty` were presented in `code/models/`; without concrete artifacts we cannot verify that the required data entity classes exist or contain any implementation. The implementer must add the three model classes in the specified directory and provide their contents.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

