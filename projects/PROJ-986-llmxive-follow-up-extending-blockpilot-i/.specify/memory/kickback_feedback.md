# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directories (e.g., `projects/PROJ-986-llmxive-follow-up-extending-blockpilot-i/`, `code/`, `data/raw/`, etc.) is provided; the claim lacks any tangible artifact confirming the directory structure was created.
- `T001b` (rejected 1x): No evidence of the required `__init__.py` files in `code/`, `code/utils/`, `tests/`, `tests/unit/`, `tests/integration/`, or `tests/contract/` was provided; the claim cannot be verified without the actual files. The implementer must supply the directory listings or the files themselves to confirm they exist and are empty.
- `T001c` (rejected 1x): No evidence of a `README.md` or `.gitignore` file in the project root is provided; the claim lacks any displayed artifact content or confirmation of their existence. The required placeholder files are therefore missing.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or `setup.cfg` for Ruff/Flake8) or scripts were presented. Without these artifacts, the requirement to configure Ruff/Flake8 and Black cannot be verified as fulfilled. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly set up.
- `T007` (rejected 1x): The implementer provided no files or code under a `contracts/` directory defining the required base schemas for `FeatureVector`, `GroundTruth`, `Prediction`, or `ModelArtifact`. Without these schema definitions, the task of creating the base contracts is not satisfied. The next implementer must add non‑empty schema files (e.g., Pydantic models, JSON Schema, or equivalent) for each of the four entities in the `contracts/` folder.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

