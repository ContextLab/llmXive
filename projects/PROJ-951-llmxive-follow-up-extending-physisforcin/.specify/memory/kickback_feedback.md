# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001b` (rejected 1x): No directory listings or other evidence were provided showing that `src/`, `tests/`, and `data/` actually exist under `projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/`. Without concrete proof of these subdirectories, the task requirement is not satisfied.
- `T003` (rejected 1x): declared artifact(s) missing/empty/invalid: pyproject.toml
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/seeding.py
- `T006b` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/profile_memory.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

