# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory structure (`src/`, `tests/`, `data/`, `output/`) was presented or described in the provided evidence; the implementer gave only a feature specification without showing the required folders or any files within them. Consequently the task requirement is not satisfied.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or documentation of their setup are present in the provided evidence, so the requirement to configure ruff/flake8 and Black cannot be confirmed. The implementer must add the actual configuration artifacts and demonstrate they are active in the project.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/config.py
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007` (rejected 1x): The `validate.py` file is present but its implementation is truncated and does not fully perform validation (e.g., the `validate_data` function ends abruptly). Moreover, the required `dataset.schema.yaml` file is missing, so the script cannot actually validate against a schema and will raise a `FileNotFoundError` instead of the expected `E_SCHEMA_MISSING`. The artifact therefore does not satisfy the task’s requirement.
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: src/utils/plots.py
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: src/main.py
- `T039` (rejected 1x): The required file `src/main.py` is missing entirely, so no memory‑check logic or chunked‑processing code could be present. The task’s core deliverable does not exist.
- `T040` (rejected 1x): The required file `src/main.py` is missing entirely, so no memory‑check logic could have been added. Consequently the task’s deliverable does not exist.
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/clean.py
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/clean.py
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: src/data/clean.py
- `T019` (rejected 1x): The required unit‑test file `tests/unit/test_disproportionality.py` does not exist in the repository, so no test verifying ROR/PRR/IC logic (including continuity correction) is present. Consequently the task’s deliverable is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

