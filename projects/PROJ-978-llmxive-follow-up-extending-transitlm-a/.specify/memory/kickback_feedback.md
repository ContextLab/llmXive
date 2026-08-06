# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory listings or screenshots were provided to show that the required folders (`code/`, `data/raw/`, `data/processed/`, `data/analysis/`, `models/`, `analysis/`, `tests/`, `docs/`) actually exist; the response contains only the task description without any concrete artifacts. The implementer must create and demonstrate the presence of these directories.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or similar) or related setup scripts are present in the provided evidence, so the requirement to configure Ruff and Black is not demonstrated.
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: data/preprocess.py
- `T007` (rejected 1x): The required file `data/graph_utils.py` does not exist, so no code to build the adjacency graph or perform the ≥95% edge‑overlap validation is present. The task’s core artifact is missing.
- `T009` (rejected 1x): No `config.py` file or any code defining environment configuration, random seeds, or city‑mapping constants is present in the provided artifacts. The claim cannot be verified because the required artifact is missing.
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: models/lightweight.py

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

