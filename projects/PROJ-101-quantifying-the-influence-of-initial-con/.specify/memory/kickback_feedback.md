# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (`code/`, `tests/`, `data/raw/`, `data/processed/`, `state/`) being present or created is provided; the claim lacks any artifact or file listing to verify the directory structure.
- `T001c` (rejected 1x): No evidence of the required `tests/unit/` and `tests/integration/` directories is provided; the artifact list is empty, so the claim cannot be verified. The implementer must add these two directories (with at least placeholder files) to satisfy the task.
- `T003` (rejected 1x): The submission provides only the scientific feature specification; there are no linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.flake8` or `.ruff.toml`, or pre‑commit hook definitions) present in the evidence. Consequently, the requirement to configure ruff/flake8 and Black is not satisfied. Adding the appropriate config files and confirming they are active would be needed.
- `T007` (rejected 1x): No code, module, or documentation for a “base utility for numerical stability checks” (convergence detection, boundedness checks) was presented. The only artifacts described relate to trajectory generation and FTLE computation, not to the required utility, and there is no file path or content to verify. The task therefore lacks the required implementation.
- `T008` (rejected 1x): No pytest configuration or fixture code (e.g., a `conftest.py` defining a seed fixture and a temporary‑directory fixture, or a `pytest.ini`/`pyproject.toml` entry) was provided. Without these artifacts the claim that the task “Configure `pytest` with fixtures for random seeds and temporary data directories” cannot be verified. The required pytest fixture implementations are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

