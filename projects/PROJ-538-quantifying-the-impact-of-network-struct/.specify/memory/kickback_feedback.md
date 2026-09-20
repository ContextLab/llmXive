# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of a `projects/PROJ-538-quantifying-the-impact-of-network-struct/` directory or any files within it was provided; the claim lacks any tangible artifact to verify that the required project structure was created.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or Black settings) or any evidence of them being set up are present. The claim provides no artifacts demonstrating that ruff/flake8 and Black have been configured, so the task requirement is not satisfied.
- `T004` (rejected 1x): No evidence of a `data/` directory with the required subfolders (`raw/`, `processed/`, `contracts/`) is provided; the implementer did not supply any file system listing, screenshots, or code that creates these directories. The task remains undone until the directory structure is created and verified.
- `T009` (rejected 1x): No evidence of a `tests/` directory, test files, or a pytest configuration (e.g., `pytest.ini`, `pyproject.toml` with `pytest-cov` settings) was provided, so the required pytest framework with coverage integration is not demonstrated. The implementer must add the test suite and proper pytest‑cov configuration.
- `T013` (rejected 1x): The repository lacks a `RealDataLoader` implementation in `code/ingest.py` (the file only defines `DefectGraphBuilder` and is truncated before any loader logic). Additionally, the required output file `data/processed/raw_snapshots.parquet` does not exist. Consequently, the task’s specifications are not met.
- `T034` (rejected 1x): The required output file `data/processed/correlation_heatmap.png` is missing, so the verification conditions (existence, 300 DPI, labeled grid) cannot be satisfied. The implementation in `code/viz.py` exists, but without the generated image the task is not completed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

