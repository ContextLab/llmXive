# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`src/`, `tests/`, `data/`, `docs/`, `config/`) is provided; the response contains only a feature specification and no actual project‑structure artifacts. The task therefore remains unfinished.
- `T003` (rejected 1x): No linting (ruff) or formatting (black) configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`) or related setup scripts were provided, so the required artifact does not exist or is empty. The task remains unfulfilled.
- `T006b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/download.py
- `T020` (rejected 1x): No code, data files, or logs were supplied; the implementer did not provide the required data acquisition/preprocessing pipeline script, the processed CSV, or any evidence (e.g., logs, schema validation) that the pipeline meets the detailed acceptance criteria. Consequently the task’s core deliverable is missing.
- `T029` (rejected 1x): No README.md content was supplied or referenced, so there is no evidence that quickstart instructions and execution commands were added. The required artifact is missing, preventing verification that the task was fulfilled.
- `T030` (rejected 1x): No `.gitignore` file or GitHub Actions workflow (e.g., `.github/workflows/ci.yml`) was presented or referenced in the provided evidence, so the required artifacts for adding a CPU‑only CI configuration are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

