# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence was provided that the `data/` and `data/defects4j/` directories actually exist on disk; the implementer did not include any directory listings, creation scripts, or screenshots confirming their presence. The required artifact is missing.
- `T002` (rejected 1x): No evidence was provided that the `code/`, `code/utils/`, or `code/models/` directories actually exist in the repository; the response contains only the task description and specifications, with no file‑system listing or screenshots showing those directories. The required directory structure is therefore missing.
- `T003` (rejected 1x): No evidence was provided that the `explanations/`, `state/`, or `tests/` directories actually exist in the repository; the response contains only the task description and no file‑system listing or screenshots confirming the directories were created. The implementer must add the required directories (and optionally a brief README) to satisfy the task.
- `T005` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or Black settings) or setup scripts are present in the provided evidence, so the requirement to configure ruff and black is not satisfied. The implementer must add the appropriate configuration files and any integration steps (e.g., pre‑commit hooks).
- `T006b` (rejected 1x): No spec.md content is provided, so we cannot confirm that FR-006 was replaced with FR-006-REV, that US‑2 Acceptance Scenario 3 now outputs `coherence_score`, or that SC‑007 defines the cosine‑similarity range. The required artifact (the amended specification file) is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

