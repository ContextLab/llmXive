# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings, `.gitkeep` files, or any other evidence of the required `code/`, `data/`, `results/`, `tests/`, and `docs/` folders under `projects/PROJ-294-evaluating-the-impact-of-code-generation/` were provided. The implementer’s claim cannot be verified without concrete artifacts.
- `T001b` (rejected 1x): No evidence of a `state/` directory inside `projects/PROJ-294-evaluating-the-impact-of-code-generation/` is provided; the artifact list is empty, so the required directory was not shown to exist.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

