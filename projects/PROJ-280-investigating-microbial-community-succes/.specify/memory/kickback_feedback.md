# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001a` (rejected 1x): No evidence of the required directory tree (`projects/PROJ-280-investigating-microbial-community-succes/` with subfolders `data/raw`, `data/processed`, `data/config`, `code`, `tests/unit`, `tests/contract`, `tests/integration`, `state/projects`, and `contracts`) is presented. The implementer’s claim cannot be verified because the actual filesystem artifacts are missing.
- `T001b` (rejected 1x): No `MANIFEST.txt` file was presented in `projects/PROJ-280-investigating-microbial-community-succes/`, nor any listing of its contents; thus the required artifact is missing. The task cannot be considered completed until a non‑empty manifest file enumerating all files/directories from T001a is provided.
- `T003` (rejected 1x): I examined the provided evidence and found no linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or a `pre-commit` config) inside `projects/PROJ-280-investigating-microbial-community-succes/`. Without these artifacts, the task of configuring flake8/black is not satisfied. The implementer must add the appropriate configuration files and ensure they are non‑empty and correctly set up.
- `T004` (rejected 1x): The provided `data/config/dataset_ids.json` exists and is non‑empty, but the required schema validator (and the referenced `contracts/dataset-config.schema.yaml` that defines the schema) are missing, so the task of creating a validator and sample config per that schema is not fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

