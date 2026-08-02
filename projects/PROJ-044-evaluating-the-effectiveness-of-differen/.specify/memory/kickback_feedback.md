# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory tree (`code/data`, `code/training`, `code/analysis`, `code/models`, `tests/unit`, `tests/integration`, `data/raw`, `data/partitions`, `results`, `artifacts`) inside `projects/PROJ-044-evaluating-the-effectiveness-of-differen/` is provided; the implementer’s claim is unsubstantiated. The missing folder structure must be created and shown (e.g., via a directory listing).
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- `T011` (rejected 1x): The repository lacks the required `data/raw/femnist.parquet` and its corresponding `femnist.sha256` checksum files, and the provided `code/data/download.py` is truncated and does not contain a concrete FEMNIST download implementation that writes those files. Consequently the task’s core deliverables are missing.
- `T011b` (rejected 1x): The required `data/raw/shakespeare.parquet` and its `.sha256` checksum are absent, and the provided `code/data/download.py` is truncated and does not contain a concrete implementation that downloads the `leaf/shakespeare` dataset and writes those files. The task’s core deliverables are therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

