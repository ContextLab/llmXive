# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required project directories (`code/`, `tests/`, `data/`, `specs/`) is provided; the implementer did not supply any file listings or contents showing that these folders exist and contain files. The task cannot be considered fulfilled until the specified structure is present in the repository.
- `T003` (rejected 1x): The provided information contains only the feature specification and user stories; there are no files, configuration snippets, or scripts shown that set up ruff linting or black formatting (e.g., a `pyproject.toml` with black settings, a `.ruff.toml`, or a CI step invoking them). Without such artifacts, the requirement to configure linting and formatting tools is not satisfied. The implementer must add the appropriate configuration files and/or documentation demonstrating that ruff and black are integrated into the project.
- `T004` (rejected 1x): The claim provides no visible `.gitignore` or `.env.example` files, nor any content showing they were created. Without these non‑empty artifacts present, the requirement to set up ignore rules and environment variable templates is not satisfied. The next implementer must add a proper `.gitignore` and a populated `.env.example` file to the repository.
- `T009` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T019` (rejected 1x): No trained DistilBERT model file or checkpoint is present in `code/models/router_model/`, nor is there any training script, logs, or evidence that the router was trained on the CSV from T013. The required artifact is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

