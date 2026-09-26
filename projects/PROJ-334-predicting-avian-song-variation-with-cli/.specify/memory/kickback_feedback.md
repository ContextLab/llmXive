# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): The implementer only supplied a feature specification and user stories; there is no evidence of a Python project being created, nor any files (e.g., `pyproject.toml`, `requirements.txt`, `setup.cfg`, or a virtual environment) listing the required dependencies. Consequently, the core task of initializing the project with the specified packages is not satisfied.
- `T003` (rejected 1x): The implementer provided no linting or formatting configuration files (e.g., `pyproject.toml` entries for Black, a `.ruff.toml` or `ruff.toml`, or any related setup scripts). Without these artifacts, the requirement to configure ruff and Black is not satisfied. The next implementer must add the appropriate configuration files and ensure they are non‑empty and correctly set up.
- `T004` (rejected 1x): declared artifact(s) missing/empty/invalid: data/checksums.txt, state/projects/PROJ-334-predicting-avian-song-variation-with-cli.yaml
- `T005` (rejected 1x): No configuration loader code or files were presented; the evidence consists only of a project specification unrelated to a base configuration loader. Consequently, the required artifact (a loader handling environment variables and paths) is missing.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T011` (rejected 1x): declared artifact(s) missing/empty/invalid: data/checksums.txt, state/projects/PROJ-334-predicting-avian-song-variation-with-cli.yaml
- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: data/checksums.txt, state/projects/PROJ-334-predicting-avian-song-variation-with-cli.yaml
- `T013` (rejected 1x): The repository lacks the required `contracts/*.schema.yaml` file, so validation cannot be performed, and the `reproject_dataset` function contains only a placeholder with no logic to read CRS metadata or infer mismatches. Consequently, the ingestion script does not meet the explicit CRS‑detection and reprojection requirements.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

