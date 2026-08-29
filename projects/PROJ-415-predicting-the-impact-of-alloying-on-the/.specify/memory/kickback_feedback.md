# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of the required directories (`code/`, `tests/`, `data/`, `models/`, `reports/`) is provided; the artifact list is empty, so the project structure has not been demonstrated.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `pyproject.toml` with Black/Ruff settings, `.flake8` config, or a `requirements-dev.txt` including these tools) or setup scripts are present in the provided evidence. Consequently, the task of configuring ruff/flake8 and Black has not been demonstrated.
- `T007` (rejected 1x): No `data/` directory with the required subfolders (`raw/`, `curated/`, `artifacts/`) is present, nor any script or code implementing checksum generation/verification for files in those folders. The implementer provided only narrative text without the actual filesystem changes or checksum logic, so the task is not satisfied.
- `T008` (rejected 1x): The required output file `data/raw/fetched_diffusion.csv` is missing, and the provided `acquisition.py` contains placeholder logic and comments about “simulating” diffusion values rather than actually fetching and writing real data as specified. The script does not demonstrably save a CSV or log the exact warning message when N < 50.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

