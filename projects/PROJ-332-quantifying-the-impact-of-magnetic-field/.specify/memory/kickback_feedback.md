# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `data/raw/`, `data/processed/`, `artifacts/`, `tests/`) is presented; without confirming their existence and non‑emptiness, the task’s core requirement is unmet. The implementer must add the specified project structure to the repository.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) are present in the provided evidence, so the requirement to configure flake8/black is not satisfied. The implementer must add the appropriate configuration artifacts.
- `T006` (rejected 1x): `code/utils/limits.py` defines timeout and memory guard utilities, and `code/main.py` imports and applies them to the pipeline function. However, the required GitHub Actions workflow file `.github/workflows/ci.yml` is absent, so the CI‑level timeout configuration is not present. The missing workflow file must be added and configured for the task to be complete.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T013` (rejected 1x): No code, script, or module was presented that accesses MDSplus to fetch `island_width`, checks for its presence, derives it via the Rutherford equation using `local magnetic shear`, `q`, and `Bt`, logs warnings, or excludes discharges as specified. Without any artifact, the requirement is not satisfied.
- `T014b` (rejected 1x): The required schema files `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` are missing, and the `validator.py` implementation is incomplete (truncated code and no logic that actually loads or validates against those specific contracts before any parsing). The task’s core requirement is therefore not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

