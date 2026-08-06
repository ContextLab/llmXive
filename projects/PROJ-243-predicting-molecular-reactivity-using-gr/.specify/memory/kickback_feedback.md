# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence was presented showing that a `data/raw` directory exists in the repository, nor any contents inside it. Without a visible directory (or at least a placeholder file), the requirement to create the data directory is not satisfied. The next implementer should add the `data/raw` folder (e.g., with a `.gitkeep` file) and ensure it is committed.
- `T001b` (rejected 1x): No evidence was presented showing that a `data/processed` directory exists in the repository, nor any contents inside it. Without a visible directory or files, the requirement to create the processed data directory is not satisfied.
- `T001c` (rejected 1x): No evidence of a `data/assets` directory (or any files within it) is provided; the required artifact is missing. The implementer must create the `data/assets` folder and ensure it contains the expected data files.
- `T002` (rejected 1x): No evidence was provided showing that the required directories (`code`, `artifacts`, `tests`) actually exist or contain any files; without such artifacts the claim cannot be verified.
- `T004` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `ruff.toml`, `pyproject.toml` with Black settings) or related setup scripts are present in the provided evidence, so the requirement to configure flake8/ruff and Black has not been satisfied.
- `T009` (rejected 1x): No evidence of a logging setup (e.g., configuration files, code that writes structured logs, or the required `artifacts/logs/` directory and `artifacts/metrics.json` file) was provided. The task’s deliverables are missing, so the requirement is not satisfied.
- `T010h` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/reference_substructures_raw.csv, data/raw/kinetic_dataset_raw.csv, data/raw/checksums.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

