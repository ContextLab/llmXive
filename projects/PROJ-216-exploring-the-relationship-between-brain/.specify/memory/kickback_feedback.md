# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): No `specs/amendment-001-fluid-intelligence-n10.md` file was presented, and no excerpt of its contents was shown. Without the required markdown file containing the exact specified text, the task’s deliverable is missing.
- `T005` (rejected 1x): Only `contracts/download_contract.yaml` exists and contains the required `input`/`output` sections; the other three contract files (`preprocess_contract.yaml`, `graph_contract.yaml`, `stats_contract.yaml`) are missing entirely. The task requires all four contract files to be present with proper schemas.
- `T006` (rejected 1x): No `data-model.md` file was presented, and there is no evidence that it exists or contains the required entity definitions for `Subject`, `GraphMetric`, and `BehavioralScore`. The implementer must add the markdown file with the specified attributes and types.
- `T007` (rejected 1x): No `quickstart.md` file is presented or described in the provided evidence, and no contents showing step‑by‑step reproducible instructions are available. The required documentation artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

