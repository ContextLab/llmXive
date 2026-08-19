# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings or screenshots were provided showing the required folders (`code/`, `data/`, `data/raw`, `data/processed`, `data/logs`, `tests/`, `artifacts/`, `figures/`). Without concrete evidence that these directories exist and are non‑empty, the claim cannot be verified. The implementer must supply a file‑system view (e.g., `tree` output or a zip archive) confirming the full structure.
- `T001c` (rejected 1x): No `.gitignore` file was presented in the evidence; the implementer did not supply the required artifact, nor any content showing that a Python‑and‑data‑artifact ignore list was created. The task remains undone.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `ruff.toml`, `.flake8`, or CI scripts invoking ruff/flake8/black) are present in the provided artifacts, so the task of configuring these tools is not satisfied. The implementer must add the appropriate configuration files and ensure they are functional.
- `T004` (rejected 1x): No evidence of a `code/utils/` directory or an `__init__.py` file was provided; the claim cannot be verified without those artifacts present. The required directory and initialization file are missing.
- `T007a` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009` (rejected 1x): No `.env` file, configuration script, or documentation for handling API keys is present in the provided evidence; the task required concrete environment configuration management artifacts, which are missing.
- `T025` (rejected 1x): declared artifact(s) missing/empty/invalid: figures/feature_importance.png

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

