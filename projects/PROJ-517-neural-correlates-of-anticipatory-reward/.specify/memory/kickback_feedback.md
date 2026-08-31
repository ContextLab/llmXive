# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was presented that the required `code/` and `tests/` directories actually exist in the project repository; the claim is unsupported and the artifact is missing. The implementer must create these two directories at the project root.
- `T001b` (rejected 1x): No evidence was provided that the required directories (`data/raw/`, `data/processed/`, `data/figures/`) actually exist in the project repository; the claim is unsubstantiated. The implementer must create these folders (or show a directory listing) to satisfy the task.
- `T001c` (rejected 1x): No evidence was presented that the required directory `specs/001-neural-correlates-of-anticipatory-reward/` actually exists in the repository (or contains any files). Without confirming the presence of this spec directory, the task cannot be considered completed.
- `T002b` (rejected 1x): declared artifact(s) missing/empty/invalid: projects/PROJ-517-neural-correlates-of-anticipatory-reward/requirements.txt

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

