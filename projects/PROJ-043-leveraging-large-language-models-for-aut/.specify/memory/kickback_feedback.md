# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of a `code/` directory at the repository root is provided; the artifact list is empty, so the required directory has not been demonstrated as existing. The implementer must add the `code/` folder (non‑empty) to satisfy the task.
- `T001b` (rejected 1x): No evidence was provided that a `data/` directory exists at the repository root; the claim lacks any artifact (e.g., directory listing, screenshot, or file) confirming its creation. The required directory is missing from the supplied information.
- `T001c` (rejected 1x): No artifact showing a `tests/` directory at the repository root was provided; without evidence of the directory’s existence, the requirement cannot be confirmed as satisfied. The implementer must add proof (e.g., a directory listing or a file inside `tests/`).
- `T001d` (rejected 1x): No evidence of a `paper/` directory at the repository root is provided; the artifact list is empty, so the required directory has not been demonstrated as existing. The implementer must add the `paper/` folder to satisfy the task.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: pyproject.toml, ruff.toml
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009` (rejected 1x): The required artifact `tests/unit/test_static_analysis.py` does not exist in the repository, so no unit test for metric calculation is present. The task cannot be considered completed until this file is added with appropriate tests.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

