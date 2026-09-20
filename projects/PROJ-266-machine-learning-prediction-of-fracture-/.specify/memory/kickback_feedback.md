# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): No `research.md` file was presented in `projects/PROJ-266-machine-learning-prediction-of-fracture-/`, nor any excerpt showing the required headings (“Introduction”, “Methodology”, “Resolution Limits”, “Results”, “Discussion”). Without the actual file or its contents, the verification script cannot succeed, so the task is not satisfied. The implementer must add the `research.md` artifact with the specified section headings.
- `T006a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

