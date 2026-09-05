# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was provided showing that `code/` and `tests/` directories actually exist in the repository (or contain any files). The implementer’s claim cannot be verified without such artifacts. The next implementer should create the two directories at the repository root and ensure they are present in the project’s file tree.
- `T001b` (rejected 1x): No evidence was provided showing that the `data/raw`, `data/processed`, and `data/models` directories exist in the repository root; without visible directory listings or files, the requirement cannot be confirmed. The implementer must add the three directories (even if empty) to the project and show their presence.
- `T005b` (rejected 1x): declared artifact(s) missing/empty/invalid: state/projects/PROJ-214-decoding-emotional-valence-from-facial-e.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

