# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings or screenshots were provided to demonstrate that `code/`, `data/raw/`, `data/processed/`, `data/results/`, and `tests/` actually exist; the claim is unsupported. The implementer must supply concrete evidence (e.g., a `tree` output, `ls -R` listing, or a script showing the directories were created) to verify the task is completed.
- `T007a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

