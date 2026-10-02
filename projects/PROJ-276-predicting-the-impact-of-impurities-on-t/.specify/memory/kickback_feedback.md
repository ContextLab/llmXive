# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000` (rejected 1x): No `state/contradictions/FR-006-runtime-bug.md` file is present, nor any evidence that a time‑limit enforcement was added to subsequent tasks. The required documentation and enforcement are missing.
- `T001` (rejected 1x): No directory tree or listing was provided to confirm that the required folders (`src/ingestion`, `src/modeling`, `src/visualization`, `src/utils`, `tests/contract`, `tests/integration`, `tests/unit`, `data/raw`, `data/processed`, `docs`) were actually created. The implementer must supply evidence (e.g., a printed `tree` or `ls -R` output) showing these paths exist.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, a pre‑commit hook file, or any script invoking Ruff/Black) were presented. Without these artifacts, the claim that linting and formatting tools are configured cannot be verified. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly set up.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/constants.py
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/logging.py
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/data_provenance.py, tests/unit/test_provenance.py
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: tests/unit/test_constants.py, tests/unit/test_logging.py
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/config.py
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: src/ingestion/download_materials_project.py
- `T013` (rejected 1x): The required `src/ingestion/download_supercon.py` file does not exist, and the provided `tests/unit/test_ingestion.py` only contains data‑filtering tests unrelated to downloading the SuperCon dataset or checking for a failure when >50 % of entries lack impurity columns. No unit test verifies that the script exits with code 1 under the specified condition.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: src/ingestion/preprocess.py
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: src/modeling/train.py
- `T019` (rejected 1x): declared artifact(s) missing/empty/invalid: src/modeling/train.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

