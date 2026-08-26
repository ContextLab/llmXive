# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listing or any file system evidence was provided showing that the required folders (`code/`, `data/`, `data/raw/`, `data/processed/`, `data/analysis/`, `tests/`, `contracts/`, `state/`) actually exist; the claim is unsubstantiated.
- `T002` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` entries, `.ruff.toml`, `.flake8`, or `black` settings) were provided, nor any documentation showing that ruff/flake8 and black have been set up for the project. Consequently, the required artifact to satisfy task T002 is missing.
- `T003` (rejected 1x): No pre‑commit configuration files (e.g., `.pre-commit-config.yaml`), hook scripts, or documentation of linting/formatting tools are present. The required artifact to show that pre‑commit hooks have been set up and are functional is missing.
- `T006a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/networks.csv, schema.yaml
- `T006b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/energy_decay.csv, schema.yaml
- `T006c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/analysis/regression_results.json, schema.yaml
- `T016` (rejected 1x): No code, test, or documentation showing that error handling for generation failures was added, that specific graph IDs are logged, or that failed graphs are excluded from the final dataset is present. The required artifact (updated generation script with logging and exclusion logic) is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

