# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No repository skeleton directories (`src/`, `tests/`, `data/`, `results/`, `docs/`, `contracts/`) are present in the provided evidence; the implementer supplied only a textual claim without any actual folder structure or files. The required artifact is missing.
- `T003` (rejected 1x): No `renv.lock` file, R project initialization script, or any evidence of the listed Bioconductor packages being installed is provided. The required artifact (a reproducible R environment setup) is missing, so the task is not satisfied.
- `T004` (rejected 1x): The claim provides no linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.ruff.toml`, `.style.yapf`, or similar) and no evidence that `ruff`, `black`, or `styler` have been added to the project. The artifacts listed are unrelated to the linting task, so the required configuration is missing.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: github/workflows/ci.yml
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/logger.py
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: species.yaml, parameters.yaml
- `T010` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

