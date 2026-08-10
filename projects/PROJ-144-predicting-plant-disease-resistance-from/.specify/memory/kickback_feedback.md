# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `data/raw`, `data/processed`, `tests/`, `state/`) was provided; without a directory listing or files, we cannot confirm that the project structure exists. The implementer must create and show these folders (and at least placeholder files) to satisfy the task.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/batch_corrected_matrix.csv, data/processed/labels.csv
- `T022` (rejected 1x): No code, script, notebook, or other artifact implementing VIF calculation and flagging metabolites with VIF > 5 is present; the only information is the task description itself, which does not constitute the required implementation.
- `T023` (rejected 1x): No output documentation artifact was provided that demonstrates the findings are framed as “associational.” Without a report, summary, or any written results to inspect, we cannot verify that the implementer has ensured all findings are presented in an associational manner as required by FR‑011. The required artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

