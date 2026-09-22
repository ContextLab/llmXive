# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory structure (`src/`, `tests/`, `data/`, `specs/001-gene-regulation/`) was presented or listed, and no files were shown to confirm their existence. The implementer provided no tangible evidence that the required project folders were created.
- `T003` (rejected 1x): No linting or formatting configuration artifacts (e.g., `pyproject.toml`, `.ruff.toml`, `black` settings, or CI integration scripts) are present in the provided evidence, so the requirement to configure ruff and black is not demonstrated. The implementer must add the actual configuration files and any related setup instructions.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

