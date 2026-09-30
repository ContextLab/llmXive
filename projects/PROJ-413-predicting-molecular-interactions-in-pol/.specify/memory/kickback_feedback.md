# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the `projects/PROJ-413-predicting-molecular-interactions-in-pol/` directory or its subfolders (`data/raw`, `data/curated`, `data/processed`, `code/data`, `code/models`, `code/analysis`, `code/utils`, `results`, `analysis`, `docs`, `tests/contract`, `tests/integration`) is provided. The required directory tree must be created and shown (e.g., via a directory listing) to satisfy the task.
- `T001b` (rejected 1x): No evidence of a Git repository being initialized in the specified path nor a `.gitignore` file for Python is present; the required artifacts are missing.
- `T005` (rejected 1x): The `code/utils/logger.py` defines a `PerformanceLogger` but the snippet is truncated before the `_save` method that actually writes to `results/performance.json`, and the `results/performance.json` file is missing entirely. Without a functioning save routine and the required output file, the logging infrastructure is not fully set up.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

