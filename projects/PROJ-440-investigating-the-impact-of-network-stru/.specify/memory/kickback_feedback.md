# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory listing or other evidence was provided showing that the required folders (`code/`, `data/`, `data/raw/`, `data/processed/`, `data/analysis/`, `tests/`, `contracts/`, `state/`) actually exist; without such artifacts the claim cannot be confirmed.
- `T002` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.flake8` config, or related CI scripts) are present in the provided evidence, so the required artifact for configuring ruff/flake8 and black does not exist. The implementer must add the appropriate configuration files and ensure they are functional.
- `T003` (rejected 1x): No pre‑commit configuration files (e.g., `.pre-commit-config.yaml`, hook scripts, or documentation of hook installation) are present in the provided artifacts, so the requirement to configure linting/formatting hooks is not satisfied. The claim lacks any concrete evidence of the requested setup.
- `T006a` (rejected 1x): The required file `contracts/network_schema.schema.yaml` is absent from the repository, so no schema definition is provided despite the presence of `data/raw/networks.csv`. The task explicitly demands this schema file, which is missing.
- `T006b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/energy_decay.csv, schema.yaml
- `T006c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/analysis/regression_results.json, schema.yaml
- `T008` (rejected 1x): No `data/` directory with the required `raw/`, `processed/`, and `analysis/` subfolders was provided, nor any checksumming utility scripts or files. The implementer’s claim lacks any tangible artifact to verify that the directory structure and utilities were actually created.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

