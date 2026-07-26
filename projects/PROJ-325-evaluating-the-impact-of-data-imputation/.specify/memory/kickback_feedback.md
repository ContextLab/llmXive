# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (code/, data/raw, data/processed, tests/) is provided; the implementer did not supply any artifact showing that the project structure was created.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings, or a pre‑commit hook) were provided or referenced, so the required artifact for configuring ruff/flake8 and Black does not exist. The task therefore remains unfinished.
- `T005` (rejected 1x): The required synthetic dataset file `data/processed/synthetic_mar_v1.csv` is not present, and the referenced schema `contracts/dataset.schema.yaml` is also missing, so the code cannot be verified to produce output that conforms to the schema. The next implementer must generate the CSV artifact (and optionally run the script) and provide the missing schema file.
- `T006` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

