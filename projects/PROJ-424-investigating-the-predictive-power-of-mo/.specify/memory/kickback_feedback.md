# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listing or file tree was provided showing the required `code/`, `data/raw/`, `data/processed/`, `data/interim/`, `tests/unit/`, and `tests/integration/` folders under `projects/PROJ-424-investigating-the-predictive-power-of-mo/`. Without concrete evidence of these directories, the task requirement is not satisfied.
- `T002` (rejected 1x): declared artifact(s) missing/empty/invalid: projects/PROJ-424-investigating-the-predictive-power-of-mo/requirements.txt
- `T003` (rejected 1x): No linting (ruff) or formatting (black) configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`) or related setup scripts are present in `projects/PROJ-424-investigating-the-predictive-power-of-mo/`. Without such artifacts, the claim of having configured the tools cannot be verified.
- `T008a` (rejected 1x): No updated `spec.md` file (or excerpt showing FR‑008 with the R² threshold changed to 0.95) is provided. The claim lacks the required artifact demonstrating the specification change, so the task is not satisfied.
- `T008b` (rejected 1x): No updated `spec.md` file was provided; the claim that SC-005 was edited to replace “bootstrap difference-of-means test (p ≤ 0.05)” with “descriptive trend analysis” cannot be verified. The required artifact (the modified spec document) is missing.
- `T010` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

