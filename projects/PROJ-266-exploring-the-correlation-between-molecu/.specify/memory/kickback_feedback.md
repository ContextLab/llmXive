# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `tests/`, `data/`) is provided; the response contains only specification text and no actual project structure on disk. The task’s core deliverable is missing.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `setup.cfg`, `.flake8`, `pyproject.toml` with Black settings) or related documentation were provided. The evidence only contains a feature specification unrelated to configuring flake8/black, so the required artifact is missing.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): No directories `data/raw/` or `data/processed/` and no checksum generation script or utility are present in the provided evidence; thus the required artifact is missing. The task’s core deliverable – a ready‑to‑use directory layout plus a checksum tool – has not been supplied.
- `T012` (rejected 1x): The test file `tests/contract/test_dataset.py` exists, but it depends on `specs/001-molecular-flexibility-permeability/contracts/dataset.schema.yaml`, which is missing, so the contract tests cannot be executed. The required schema artifact must be added (and contain the expected definitions) for the task to be satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

