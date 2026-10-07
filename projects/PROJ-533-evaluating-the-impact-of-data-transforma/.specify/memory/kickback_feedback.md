# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No artifact showing that a `code/` directory was created or that its existence was verified with `test -d code` is provided; the claim cannot be confirmed from the available evidence. The implementer must supply proof (e.g., command output, screenshot, or a script that creates the directory and checks it).
- `T001b` (rejected 1x): No evidence was provided that a `data/` directory was actually created or that its existence was verified with `test -d data`; the implementer supplied no script, command output, or filesystem snapshot showing the required directory.
- `T003a` (rejected 1x): No `.flake8` file was presented in the evidence, and there is no proof that a file with the required `max-line-length=100` and the specified ignored codes exists in the repository. The implementer must provide the actual `.flake8` file containing the correct configuration.
- `T009` (rejected 1x): The provided `code/utils/logging_config.py` defines a `JSONFormatter` and an `AtomicFileHandler` that ensures the log directory exists and attempts file locking, but it never creates or configures a logger that writes specifically to `results/pipeline.log`, nor does the shown code implement the required atomic‑write‑via‑temp‑file‑then‑rename logic (the handler still inherits from `RotatingFileHandler` and no custom `emit`/`write` method is visible). Consequently the core requirements of the task are not satisfied.
- `T015` (rejected 1x): The provided `filter_datasets.py` is truncated and does not show any logic that checks a dataset’s overall missing‑value rate, excludes datasets with >10 % missing, or writes entries to `data/imputation_log.csv` or `data/exclusions.csv`. Both CSV files contain only header rows (no actual log or exclusion records). Consequently the required imputation, exclusion, and logging functionality is not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

