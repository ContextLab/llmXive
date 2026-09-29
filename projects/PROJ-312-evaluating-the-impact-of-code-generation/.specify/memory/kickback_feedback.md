# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002a` (rejected 1x): declared artifact(s) missing/empty/invalid: projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.txt
- `T002b` (rejected 1x): declared artifact(s) missing/empty/invalid: projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.txt
- `T004a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T004b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T004c` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T019d` (rejected 1x): The only artifact shown is that `data/spot_check/annotations.csv` is missing; there is no code, log output, or final report demonstrating that a CRITICAL warning is logged, the validation status is set to 'UNVALIDATED', or that the analysis proceeds with heuristic‑only classification. These required behaviors are absent, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

