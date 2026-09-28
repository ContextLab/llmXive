# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required `code/`, `data/`, and `tests/` directories was provided; the artifact list is empty, so the project structure has not been demonstrated. The implementer must create and show these three top‑level folders (with at least placeholder files) to satisfy the task.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, or a `black` config) or setup scripts are present in the provided evidence, so the requirement to configure ruff and black is not demonstrated. The implementer must add the appropriate configuration files and ensure they are applied to the codebase.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006` (rejected 1x): No evidence of the required `data/raw/`, `data/processed/`, or `data/graphs/` directories or their `.gitkeep` placeholder files is provided; without these artifacts the task is not satisfied.
- `T007` (rejected 1x): No configuration loader code or related files were presented; the claim provides no artifact implementing environment‑variable handling or dataset‑path configuration, so the required base config loader is missing.
- `T010` (rejected 1x): declared artifact(s) missing/empty/invalid: scripts/ingest.py
- `T016` (rejected 1x): No code, CSV, or configuration changes were provided that show tasks are flagged as “Unparseable,” retained in the ground‑truth CSV with a status field, or that T015, T019, and T020 skip the tree‑sitter step for those rows. The required implementation artifacts are missing.
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: scripts/extract_features.py
- `T022` (rejected 1x): No code, script, or documentation implementing the fallback logic for “semantic_complexity” is provided; the artifact is missing entirely, so the requirement cannot be verified as satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

