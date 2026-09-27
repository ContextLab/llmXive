# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree, `__init__.py` files, or `.gitignore` content were provided; without visible evidence of the required folder structure and files, the task’s deliverable cannot be confirmed as completed. The implementer must supply the actual project layout showing all listed directories, the initialization files, and a `.gitignore` with the specified exclusions.
- `T013c` (rejected 1x): No `heartbeat_monitoring.py` file (or any code) was presented in the evidence, so the required implementation for heartbeat loss detection and task re‑assignment is missing. The task remains undone.
- `T012` (rejected 1x): No `code/orchestrator/remote_tools_manager.py` file or its contents were provided; therefore we cannot verify that the required implementation exists, is non‑empty, or fulfills the specification of verifying and installing CLI tools on remote nodes. The necessary artifact is missing.
- `T015a` (rejected 1x): No `code/orchestrator/scheduler_setup.py` file (or its contents) was presented for review, so we cannot confirm that the scheduler configuration logic was actually implemented, is non‑empty, or meets the detailed requirements described in the user stories. The required artifact is missing.
- `T015b` (rejected 1x): No `code/orchestrator/scheduler_execution.py` file or its contents were provided, and there is no evidence that the required functions `assign_chunk(chunk, node)` and `monitor_task(task_id)` have been implemented. The implementer must supply the actual script with working implementations of these functions.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

