# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or file list was provided showing that the required folders (`code`, `code/utils`, `data/raw`, `data/processed`, `tests/unit`, `tests/integration`, `docs/figures`, `state`) actually exist; the claim is unsupported by any artifact. The task remains undone.
- `T003` (rejected 1x): The provided evidence contains only high‑level feature specifications for video extraction and labeling; there is no `.pre-commit-config.yaml`, `pyproject.toml`, or any configuration files/scripts for ruff, black, or pre‑commit hooks. Consequently, the required linting/formatting setup is missing.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/chunking_config.json, data/processed/memory_log.json
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/features.npy

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

