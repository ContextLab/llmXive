# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): No `node_manager.py` file (or any non‑empty implementation) was presented in the evidence, and therefore there is no code handling SSH connections, heartbeat pings, or device discovery as required. The task remains undone.
- `T014a` (rejected 1x): No `instrumentor_remote.py` file (or its contents) was presented in the evidence, and there is no indication that the required remote‑execution logic for `tcpdump` and `mpstat` via SSH has been added to `code/orchestrator/`. The task’s core artifact is therefore missing.
- `T014b` (rejected 1x): No `code/orchestrator/mpstat_parser.py` file or its contents were provided, so we cannot confirm that a parser was implemented, that it is non‑empty, or that it correctly extracts `cpu_utilization_pct` for the `PhysicalNode` entity. The required artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

