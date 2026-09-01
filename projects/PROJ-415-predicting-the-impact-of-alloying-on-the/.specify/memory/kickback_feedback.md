# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The implementer did not provide any evidence that the required directories (`code/`, `tests/`, `data/`, `models/`, `reports/`) actually exist or contain any files; no directory listing or file contents were shown. Without concrete artifacts, the task requirement is not satisfied.
- `T003` (rejected 1x): The implementer provided no linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `.flake8` files, or any documentation showing the tools are set up and integrated). Consequently, there is no evidence that ruff/flake8 linting or Black formatting has been configured for the project. The required artifacts are missing.
- `T007` (rejected 1x): No evidence of the required `data/` subdirectories (`raw/`, `curated/`, `artifacts/`, `logs/`) or the `errors/` directory is provided, nor any code or scripts implementing checksum logic for files in `data/`. The implementer’s claim cannot be verified without these artifacts.
- `T024` (rejected 1x): declared artifact(s) missing/empty/invalid: models/final_rf.pkl, models/final_gb.pkl, models/linear_coef.json
- `T025` (rejected 1x): The `code/models/inference.py` file stops after creating the output directory and does not contain the logic to load the RF and GB models, compute the metrics, and write them to `models/metrics.json`. Consequently, the required `models/metrics.json` file is absent. The missing code and output file must be added for the task to be considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

