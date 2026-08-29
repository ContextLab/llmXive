# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`src/`, `tests/`, `data/`, `specs/001-gene-regulation/`) is provided; the claim lacks any file or folder listings to confirm the project structure exists. The implementer must create and show these directories (with at least placeholder files) to satisfy the task.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `black.toml`, or a `pre-commit` hook) are present in the provided evidence, nor any documentation showing that ruff and black have been set up for the project. The required artifact—working configuration for both tools—is missing.
- `T004` (rejected 1x): No directory listings or file contents were provided, so we cannot verify that `data/raw/`, `data/derived/`, `data/gold_standard/`, and `artifacts/` actually exist or contain any data. The implementer must add evidence (e.g., a directory tree screenshot or a manifest file) showing these folders are present and non‑empty.
- `T009b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T010a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T010b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009c` (rejected 1x): The three required files (`data/raw/gold_standard_raw.jsonl`, `data/gold_standard/human_annotations.json`, and `data/gold_standard/character_map.json`) are all missing, so no processing could have been performed and the expected output does not exist. The task therefore is not satisfied.
- `T016a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

