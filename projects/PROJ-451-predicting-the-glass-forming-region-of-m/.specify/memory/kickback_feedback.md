# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required root directory `projects/PROJ-451-predicting-the-glass-forming-region-of-m/` is present; the implementer did not provide any file or folder listing confirming the directory was created. The task therefore remains unfulfilled.
- `T001b` (rejected 1x): No evidence was presented showing that the required `code/`, `data/`, `tests/`, `docs/`, and `notebooks/` subdirectories actually exist in the repository; without directory listings or files, the claim cannot be verified.
- `T002` (rejected 1x): No linting (ruff) or formatting (black) configuration files (e.g., pyproject.toml, .ruff.toml, or black settings) or setup scripts are present in the provided evidence, so the requirement to configure these tools is not satisfied.
- `T005` (rejected 1x): No evidence of the required `data/raw/` and `data/processed/` directories or the placeholder `.gitkeep` files is provided; without these artifacts the task of setting up the directory structure cannot be confirmed as done.
- `T006` (rejected 1x): No `.env.example` file with the required placeholders or `utils/config.py` script was presented. Without these artifacts, the environment configuration management task is not satisfied. The next implementer must add the two files with proper loading and validation logic.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

