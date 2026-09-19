# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listings or file system evidence were provided showing that the required folders (`code/`, `data/`, `data/raw/`, `data/processed/`, `data/analysis/`, `tests/`, `contracts/`, `state/`) actually exist; the claim is unsubstantiated.
- `T002` (rejected 1x): The provided material only contains a feature specification for network generation and simulation; there are no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) or any evidence that ruff/flake8 and black have been set up. Consequently, the task of configuring those tools is not satisfied.
- `T003` (rejected 1x): No pre‑commit configuration files (e.g., `.pre-commit-config.yaml`), hook installation scripts, or documentation are present. The claim provides only a unrelated feature specification; it does not include the required artifact to configure linting/formatting hooks. The task remains undone.
- `T006a` (rejected 1x): The required `contracts/network_schema.schema.yaml` file is missing entirely; only the CSV data file is present. Without the schema definition, the task of drafting the contract for `data/raw/networks.csv` is not fulfilled. The next implementer must create the YAML schema file with the appropriate column definitions.
- `T006b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/energy_decay.csv, schema.yaml
- `T006c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/analysis/regression_results.json, schema.yaml
- `T016` (rejected 1x): No code, tests, or documentation were provided showing that generation failures are now caught, that the failing graph’s ID is logged, and that such graphs are omitted from the final dataset. Without any artifact demonstrating this error‑handling logic, the task requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

