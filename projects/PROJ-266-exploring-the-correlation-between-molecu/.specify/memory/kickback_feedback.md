# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): No directory artifacts (`code/`, `tests/`, `data/`) are presented; the claim provides only a textual statement without any file system evidence that the `os.makedirs` calls were executed. The required folders are therefore missing.
- `T004` (rejected 1x): No linting or formatting configuration files (e.g., .flake8, pyproject.toml with black settings, or a pre‑commit hook) are present in the provided evidence, so the requirement to configure flake8/black is not satisfied. The implementer must add the appropriate configuration artifacts and ensure they are non‑empty.
- `T008a` (rejected 1x): No code, script, or console output showing the `os.makedirs` calls or the subsequent `assert` checks is provided, and there is no evidence that the required directories actually exist. The implementer must supply the execution artifact (e.g., a Python script or notebook cell) that creates the four directories and demonstrates the assertions passing.
- `T008b` (rejected 1x): The provided `code/utils/checksum.py` is truncated (the `scan_and_register_data_files` function ends abruptly) and no `state/pending/checksums.yaml` file exists, so the utility does not actually compute checksums and write them to the required pending file. The missing code and output must be added and the script executed to generate the pending YAML file.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009` (rejected 1x): The repository lacks the required output files (`data/raw/chembl_raw.csv`, `state/pending/checksums.yaml`, and the schema file) and the `retrieval.py` script is incomplete—it does not contain logic for exponential backoff, CSV generation matching the schema, or invocation of the checksum utility. Consequently the task’s core requirements are not satisfied.
- `T010` (rejected 1x): The provided `code/data/preprocessing.py` is present but only a portion is shown; it does not demonstrate the required steps of writing `data/processed/filtered_data.csv` and invoking `code/utils/checksum.py` to create `state/pending/checksums.yaml`. Moreover, the dependent input file `data/raw/chembl_raw.csv` and the expected output files are absent, so the end‑to‑end filtering and checksum generation cannot be verified. The missing files must be added and the script must include the save‑and‑checksum logic to satisfy the task.
- `T012` (rejected 1x): The repository contains a `tests/contract/test_dataset.py` file, but it does not show the required `test_schema_compliance` function (the file is truncated and no such method is visible). Moreover, the referenced schema file `specs/001-molecular-flexibility-permeability/contracts/dataset.schema.yaml` is absent, so the test cannot actually validate against the schema. Both the test implementation and the required schema file need to be added.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

