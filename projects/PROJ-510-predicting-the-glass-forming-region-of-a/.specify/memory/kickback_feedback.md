# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No directory structure was presented; the required root folder `projects/PROJ-510-predicting-the-glass-forming-region-of-a/` and its sub‑folders `data/`, `code/`, `tests/`, and `docs/` are not shown or listed, so the core artifact the task demanded is missing.
- `T003` (rejected 1x): No linting configuration files (e.g., .flake8, pyproject.toml/black settings, pre‑commit hooks) or documentation of flake8/black setup are present. The task required delivering those artifacts, but none were provided.
- `T004` (rejected 1x): No evidence of the required `data/raw/` and `data/processed/` directories or a `.gitignore` file containing rules for large files was provided. The implementer’s claim cannot be verified without these artifacts present in the repository.
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): No code, configuration file, or test showing that the data loading step now raises an explicit error when the `matsci/glass-forming-ability` fetch fails (and that no synthetic fallback is used) was provided. Without such artifact, we cannot confirm the required error‑handling behavior is implemented.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

