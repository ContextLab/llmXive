# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001b` (rejected 1x): The implementer supplied no linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a `pre-commit` hook) and provided no evidence that such setup was performed. Consequently the required artifact for “Configure Linting and Formatting” is missing.
- `T002` (rejected 1x): No configuration file or constants definition artifact is present; the claim provides only a high‑level feature description and no concrete code, data, or placeholder values that satisfy the “Config Constants (Placeholders)” requirement. The necessary artifact is missing.
- `T003a` (rejected 1x): No script or other artifact was provided; the response contains only the task description and no code, files, or output implementing a “Hash Artifacts Utility Script.” Consequently the required artifact is missing.
- `T004` (rejected 1x): No contract schema files (e.g., JSON/YAML definitions) are present; the only evidence is a textual feature specification unrelated to creating schemas. The required schema artifacts are missing, so the task is not satisfied.
- `T005` (rejected 1x): No artifacts were provided: there is no code, dataset, or scripts that filter the SWE‑Explore data, generate synthetic ambiguous issues, implement the iterative 3‑turn agent loop, or compute the comparative metrics. Consequently the required functionality described in the user stories is not demonstrated.
- `T006` (rejected 1x): No pytest configuration files (e.g., `pytest.ini`, `conftest.py`) or contract test skeletons (test modules with placeholder tests) are present. The only provided information is a high‑level feature specification, not the required code artifacts. The task remains undone.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

