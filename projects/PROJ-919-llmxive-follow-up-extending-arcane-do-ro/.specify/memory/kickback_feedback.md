# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or file contents were provided showing that `src/`, `tests/`, `data/`, and `specs/001-gene-regulation/` actually exist in the repository. Without concrete evidence of these folders (and any files within them), the claim that the required project structure has been created cannot be verified. The implementer must add the missing directory structure (and optionally placeholder files) to satisfy the task.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.ruff.toml`, or a `requirements-dev.txt` including these tools) were provided, nor any documentation or scripts showing they have been set up and integrated into the project. The required artifacts are missing.
- `T004` (rejected 1x): No evidence of the required directories (`data/raw/`, `data/derived/`, `data/gold_standard/`, `artifacts/`) is provided; the claim lacks any artifact listing or screenshots confirming their existence or contents.
- `T008` (rejected 1x): No code, configuration, or documentation was provided that creates or demonstrates logging of experiment run IDs, timestamps, and parameter hashes. The evidence consists only of a high‑level feature specification unrelated to state‑tracking, so the required artifact is missing.
- `T009a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/gold_standard/human_annotations.json, schema.yaml
- `T010` (rejected 1x): The required file `specs/001-gene-regulation/contracts/axis.schema.yaml` (or `schema.yaml`) does not exist, so no JSON schema for `CharacterAxis` (Coarse/Fine) is provided. The task’s primary artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

