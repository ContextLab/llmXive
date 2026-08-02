# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T040` (rejected 1x): The repository contains the `code/data_loader.py` script, but the required audit artifact `data/audit/audit_report.json` is missing, and there is no evidence that the script was run under a mocked `ConnectionError`, that it exited with a non‑zero code, or that synthetic files were checked. The task’s core verification and report generation steps have not been provided.
- `T041` (rejected 1x): The required artifact `data/audit/streaming_log.json` is absent, and there is no evidence that `code/runner.py` was run with `streaming=True` or that memory usage was monitored. Without the log file, the task’s validation requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

