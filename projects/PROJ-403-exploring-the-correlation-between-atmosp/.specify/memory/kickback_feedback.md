# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or file contents were provided, so we cannot verify that the required `src/`, `tests/`, `data/`, `figures/`, `logs/`, `report/`, and `artifacts/` folders exist, nor that `src/__init__.py` and `tests/__init__.py` were created. The implementer must supply evidence (e.g., a tree view or file list) showing these directories and files.
- `T007` (rejected 1x): The repository contains `src/data/download.py` with checksum functions, but the required output file `data/metadata.yaml` is absent, and the shown code is truncated before any logic that would write metadata. Without the metadata file, the task’s requirement to store SHA‑256 checksums is not fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

