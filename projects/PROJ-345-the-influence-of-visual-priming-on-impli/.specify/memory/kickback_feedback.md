# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): No linting/formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.pre-commit-config.yaml`, or installed hook scripts) are present or referenced, so the required setup for ruff, black, and pre‑commit hooks is missing. The task therefore is not satisfied.
- `T005` (rejected 1x): No `config.py` file or its contents are present in the provided evidence; the required path definitions and random seed pinning are not demonstrated. The implementer must add a non‑empty `config.py` that defines the specified data directories and sets a fixed random seed.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: state.yaml
- `T016` (rejected 1x): No code, script, log, or data artifact demonstrating the fallback linkage derivation was provided; there is no evidence that trials are mapped to stimulus IDs, that a >10% failure rate triggers the required halt, or that the proportion of successfully linked trials meets SC‑001. The implementer must supply the implementation (e.g., a Python module or script) and output showing the mapping results and the halt condition when applicable.
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/linked_trials.csv
- `T018` (rejected 1x): declared artifact(s) missing/empty/invalid: state.yaml
- `T023` (rejected 1x): The required output file `data/processed/confounding_report.json` does not exist, and the provided `code/data/preprocess.py` shows no implementation of a confounding check or JSON report generation. Consequently the task’s deliverable is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

