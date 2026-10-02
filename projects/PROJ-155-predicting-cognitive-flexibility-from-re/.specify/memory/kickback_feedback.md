# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required project directories (`code/`, `data/`, `docs/`, `tests/`) is provided—there is no `tree code/` output or any listing showing those folders exist. The implementer must supply a directory listing confirming the structure.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: ruff.toml
- `T004b` (rejected 1x): No `plan.md` file or its contents were provided, so we cannot confirm that the “Constitution Check” table now includes “DEVIATION (Justified in technical-design.md)” nor that the “Complexity Tracking” table marks “AR Surrogate Null Model” as “REJECTED”. The required artifact and its updated entries are missing.
- `T004c` (rejected 1x): No `plan.md` file or grep output was provided, and there is no evidence that the garbled text in the Constitution Check table was replaced with the required justification. The required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

