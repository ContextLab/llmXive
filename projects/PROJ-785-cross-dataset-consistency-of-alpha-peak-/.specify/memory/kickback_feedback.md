# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directory tree (`code/`, `tests/`, `data/raw`, `data/derivatives`, `data/processed`, `state/`) is provided; the only artifact shown is a feature specification, not the filesystem structure. The implementer must create and show these directories (non‑empty or at least existent) to satisfy the task.
- `T000` (rejected 1x): No `state/constitutional_override.md` file was presented; without the file we cannot confirm it exists, is non‑empty, or contains the required declaration that Spec FR‑002 overrides Constitution Principle VII for Pipeline B. The implementer must add the markdown file with the appropriate documentation.
- `T004` (rejected 1x): No evidence of the required Python files (`code/models/EEGDataset.py`, `APFResult.py`, `VarianceComponent.py` or equivalent) was provided, nor any content showing that these classes conform to the schemas in `contracts/`. The implementer must add the model files with the specified entities and ensure they match the contract definitions.
- `T005` (rejected 1x): No logging configuration code, scripts, or example log output were presented; there is no artifact showing that structured logs are written to the `state/` directory and the console as required. The task therefore lacks the necessary deliverable.
- `T006` (rejected 1x): No configuration artifacts (e.g., a YAML/JSON settings file, environment variable definitions, or a script that registers dataset IDs and processing parameters) were presented. Without such files or code, the requirement to “setup environment configuration management for dataset IDs and processing parameters” is not satisfied. The implementer must provide the actual configuration management implementation.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

