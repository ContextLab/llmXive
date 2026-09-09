# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence was provided that the required directories (`code`, `code/utils`, `data/raw`, `data/processed`, `tests/unit`, `tests/integration`, `docs/figures`, `state`) were actually created; the response contains only the task description and no filesystem artifacts. The implementer must supply proof (e.g., a directory listing or screenshots) that the specified project structure exists.
- `T003` (rejected 1x): The provided evidence contains only a feature specification for video model extraction and labeling; there are no files such as a `pyproject.toml`, `ruff.toml`, `.pre-commit-config.yaml`, or any scripts showing that ruff and black have been configured or added as pre‑commit hooks. Consequently, the required linting/formatting setup is missing.
- `T008` (rejected 1x): The provided material contains only the feature specification and user stories for data extraction and labeling; there are no code, configuration files, or documentation showing that error handling, logging infrastructure, or a “FAIL LOUDLY” mechanism for data fetching has been implemented. Consequently, the required artifact for task T008 is missing.
- `T013` (rejected 1x): No script, code, or output files were provided that demonstrate a `torch.no_grad()` inference pipeline extracting latent vectors and binary expert masks from intermediate DiT layers, nor any saved NumPy arrays confirming the required data. The necessary artifact (the extraction script and its non‑empty results) is missing.
- `T014` (rejected 1x): No code, script, or documentation implementing the frame‑subsampling/temporal‑chunking strategy was provided, nor any logs or output showing that video clips are processed within a 7 GB RAM limit. Without these artifacts, the requirement cannot be confirmed as met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

