# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/` (or any files within it) was provided; without confirming the project structure exists, the task cannot be considered completed.
- `T003` (rejected 1x): No linting (ruff) or formatting (black) configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`) or related setup scripts are provided or referenced, so the required artifact for configuring these tools is missing.
- `T004` (rejected 1x): No evidence of the required directories (`data/raw`, `data/processed`, `data/results`, `code/`, `tests/`) is present in the provided artifacts; the claim contains only a textual description without any actual file‑system listing or screenshots confirming the structure exists. The task therefore remains unfinished.
- `T007` (rejected 1x): The claim references creating `code/models/AdjacencyMatrix`, `HubSet`, and `CentralityScore` classes, but no such files or code snippets are present in the provided artifacts. The evidence lacks any files in `code/models/` or any definitions of the required data models, so the task is not satisfied. The implementer must add the three model files with appropriate class definitions in the `code/models/` directory.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

