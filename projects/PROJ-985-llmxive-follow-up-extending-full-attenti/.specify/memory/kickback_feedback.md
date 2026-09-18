# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or file system snapshots were provided, so we cannot confirm that the required ten directories (`code/`, `tests/`, `data/`, `code/lib/`, `code/data/`, `code/models/`, `code/evaluation/`, `data/results/`, `data/logs/`, `data/intermediate/`) actually exist and are non‑empty. The implementer must supply concrete evidence (e.g., a tree view, manifest file, or screenshots) showing these exact directories in the project.
- `T003` (rejected 1x): No configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black.toml`, or a `pre-commit` hook) or any other evidence of ruff/black being set up are present. The required artifacts that demonstrate linting and formatting tools are configured are missing.
- `T004` (rejected 1x): No pytest configuration file (e.g., `pytest.ini` or `pyproject.toml` with pytest settings) or empty test suite directory (`tests/` with placeholder test files) is present in the provided evidence. The claim that the task “Initialize pytest configuration and create empty test suite structure” is therefore not substantiated. The missing artifacts must be added for the task to be considered complete.
- `T012` (rejected 1x): The repository lacks the required `data/intermediate/attention_maps.h5` file, and the provided `extract_ground_truth.py` does not contain code that saves attention maps to that path (nor does it wrap model loading in a `torch.no_grad()` context). Consequently the core requirements of the task are not met.
- `T016` (rejected 1x): The repository lacks the required `data/logs/anomalies.csv` file, and the shown portion of `code/data/extract_ground_truth.py` does not contain any logic that detects documents with zero RTPurbo tokens, flags them, excludes them from `merged_dataset.csv`, or writes entries to an anomalies log. The task’s core requirement is therefore unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

