# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No evidence of a `projects/PROJ-516-predicting-perovskite-stability-via-comp/` directory or any files inside it is provided; the claim lacks the required project‑structure artifacts. The implementer must create the folder and populate it with the expected sub‑directories and starter files (e.g., `data/`, `src/`, `scripts/`, `README.md`, etc.) as outlined in the implementation plan.
- `T003` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `pylintrc`, `pyproject.toml` with Black/isort settings, or associated setup scripts) were presented, nor any evidence that these tools have been integrated into the project’s CI pipeline. Without such artifacts, the requirement to configure flake8/pylint and Black/isort is not satisfied.
- `T004` (rejected 1x): No `state_manager.py` file or any code that computes SHA‑256 hashes and updates the `state/...yaml` files is present in the provided evidence. The claim lacks the required artifact, so the task is not satisfied.
- `T005` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T005b` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T008` (rejected 1x): No `.env` file or any configuration snippet was presented, and there is no evidence that API keys for Materials Project and NREL have been stored securely in an environment file. The required artifact is missing, so the task is not satisfied.
- `T012` (rejected 1x): The repository contains the implemented `code/data_ingestion.py`, but the required output file `data/raw/nrel_perovskites.csv` is absent, indicating the script has not been run or does not produce the expected CSV. Without this file, the task’s core requirement—fetching, filtering for `T_d`, and writing the data—is not satisfied. The next implementer must ensure the script executes successfully and generates the non‑empty CSV at the specified path.
- `T013b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/metadata.json, schema.yaml
- `T013c` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/uncertainty_flags.json
- `T014` (rejected 1x): The repository contains a `code/feature_engineering.py` file, but the provided snippet is truncated and we cannot confirm it fully computes all required descriptors or writes them out. Moreover, the expected output file `data/processed/descriptors.csv` is absent. The missing CSV (and lack of evidence that the script produces it) means the task’s core requirement is not met.
- `T014b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/descriptors.csv
- `T017` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/descriptors.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

