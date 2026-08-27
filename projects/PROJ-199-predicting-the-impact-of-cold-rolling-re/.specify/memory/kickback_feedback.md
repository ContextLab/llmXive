# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of a `code/` directory is provided; the claim cannot be verified because the required artifact (the directory itself) is missing from the supplied evidence. The next implementer must create the `code/` folder in the repository so that `pathlib.Path(__file__).parent.joinpath('code').is_dir()` returns `True`.
- `T001b` (rejected 1x): No evidence of a `data/` directory being present in the repository is provided, nor is there any code snippet showing the `pathlib.Path(__file__).parent.joinpath('data').is_dir()` check. The implementer must add the `data/` folder (even if empty) and include a verification step confirming its existence.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

