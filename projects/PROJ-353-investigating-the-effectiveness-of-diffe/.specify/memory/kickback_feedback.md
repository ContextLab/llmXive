# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T040a` (rejected 1x): No `research.md` file in `specs/353-loss-functions-small-world/` is presented, and no content showing the hypothesis (InfoNCE vs CE) or the statistical approach (Tobit/Cox) is provided. The required artifact is missing.
- `T006a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

