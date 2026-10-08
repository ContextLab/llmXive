# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required `projects/PROJ-436-assessing-the-validity-of-statistical-si/` directory or its contents is provided; the implementer only supplied a textual description without any actual project‑structure artifacts. The task therefore remains unfinished.
- `T003` (rejected 1x): The provided evidence contains only a feature specification for statistical simulations; there are no linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.flake8`, or `black` settings) or any indication that ruff/flake8 and black have been set up. Consequently, the task “Configure linting (ruff/flake8) and formatting (black) tools” is not satisfied.
- `T004` (rejected 1x): No `code/data_loader.py` file was presented, nor any snippet showing its implementation. Consequently we cannot confirm that a script exists that uses the `openml` library to download RCT datasets and raises errors on missing IDs/files as required. The artifact is missing.
- `T005` (rejected 1x): No `code/config.py` file or its contents were presented, and there is no evidence that a module loading and validating a `SimulationConfig` (including dataset source, mechanism, rate, and outcome type) exists. The required artifact is missing, so the task is not satisfied.
- `T006` (rejected 1x): The provided evidence contains only a feature specification and no filesystem artifacts. There is no proof that the required directories `data/raw/`, `data/processed/`, `code/`, and `tests/` have been created (or contain any files). The implementer must create and show these directories to satisfy task T006.
- `T007` (rejected 1x): No JSON schema files for `SimulationConfig`, `ErrorMetric`, or `PValueDistribution` were found in a `contracts/` directory, so the required data models/contracts are missing. The task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

