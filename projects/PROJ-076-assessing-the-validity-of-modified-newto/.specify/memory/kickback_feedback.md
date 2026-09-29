# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directory hierarchy (`code/`, `data/`, `results/`, `tests/`, `state/`) is provided; the implementer’s claim lacks any artifact showing these folders exist or contain content. The task’s core requirement—creating the project structure—is therefore not satisfied.
- `T003` (rejected 1x): The review found no linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or related setup scripts in the repository. Without these concrete artifacts, the requirement to configure ruff/flake8 and Black is not satisfied. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly set up.
- `T004` (rejected 1x): The test file exists but the required schema file `contracts/dataset.schema.yaml` is missing, so the validators cannot be verified against the actual schema. Additionally, the `sample_galaxy_data` fixture creates columns of mismatched lengths, which would raise an error when the DataFrame is built, meaning the test cannot even run the validation logic. The implementation therefore does not satisfy the task’s requirement.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

