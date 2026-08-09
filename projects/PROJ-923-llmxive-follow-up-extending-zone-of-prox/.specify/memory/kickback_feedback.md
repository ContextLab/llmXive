# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree, files, or any other artifact for `projects/PROJ-923-llmxive-follow-up-extending-zone-of-prox/` was provided; therefore the required project structure per `plan.md` is missing. The implementer must create the folder and populate it with the files outlined in the plan (e.g., `README.md`, `src/`, `data/`, configuration files, etc.).
- `T003` (rejected 1x): The claim provides no linting or formatting configuration files (e.g., `pyproject.toml` with `[tool.black]` and `[tool.ruff]`, `.ruff.toml`, or CI scripts) and no evidence that ruff and black have been set up. Without such artifacts, the requirement to configure linting and formatting is not satisfied.
- `T004` (rejected 1x): The claim provides no visible files or code under a `contracts/` directory, and no schema definitions for `rollout_log`, `run_metadata`, `aggregated_metrics`, or `convergence_result` are present. Without these contract files, the task requirement is not satisfied. The next implementer should add non‑empty schema files (e.g., JSON Schema, Pydantic models, or similar) for each of the four named contracts inside a `contracts/` folder.
- `T008` (rejected 1x): No code, configuration file, or documentation establishing a deterministic random seed for all random-number generators (e.g., Python `random`, NumPy, PyTorch, TensorFlow, etc.) is present. The provided artifacts relate to ZPPO simulation and CAP mechanisms, not to seed management, so the required deterministic seed setup is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

