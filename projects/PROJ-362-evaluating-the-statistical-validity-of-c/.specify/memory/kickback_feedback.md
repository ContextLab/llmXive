# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`, or similar) are present in the provided evidence, nor any scripts or documentation showing that ruff and black have been set up for the project. The claim therefore does not satisfy the requirement to configure these tools.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T006` (rejected 1x): The provided `code/data_loader.py` only contains helper functions and a partially shown `validate_qrels_schema`; it never loads data, applies the schema validation to all records, nor logs warnings for zero‑relevance queries. Moreover, the required schema file `contracts/dataset.schema.yaml` is missing, so the validation cannot reference it. The task’s core requirements are therefore not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

