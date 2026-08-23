# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree named `projects/PROJ-191-investigating-the-validity-of-the-invers/` with the required sub‑folders is present in the provided evidence; the implementer did not supply any file‑system listing or screenshots confirming the creation of those directories. The task therefore remains unfulfilled.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, or a pre‑commit hook setup) are present in the provided evidence, nor any documentation showing that Ruff and Black have been integrated into the project workflow. Without these artifacts, the requirement to configure linting (ruff) and formatting (black) is not satisfied.
- `T007` (rejected 1x): The submission provides only a textual description of the overall project and user stories; it contains no script, command, or file‑system listing showing that the `data/raw/`, `data/processed/`, and `data/results/` directories have been created (or that `mkdir -p` logic is used). Consequently, the required artifact demonstrating the directory structure is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

