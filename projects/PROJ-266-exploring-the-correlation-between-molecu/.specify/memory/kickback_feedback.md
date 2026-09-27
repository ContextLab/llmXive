# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T002` (rejected 1x): The submission provides no tangible evidence (e.g., directory listings, screenshots, or created files) that the `code/`, `tests/`, and `data/` folders actually exist. Without such artifacts, we cannot verify that the required `os.makedirs` calls were executed. The implementer must supply proof that the three directories were created and are non‑empty.
- `T004` (rejected 1x): No linting or formatting configuration files (e.g., `.flake8`, `pyproject.toml` with Black settings, or equivalent) are present in the provided evidence, so the requirement to configure flake8/black is not satisfied. The task lacks the necessary artifact demonstrating that linting and formatting tools have been set up.
- `T008a` (rejected 1x): No artifact (e.g., script output, log, or file system listing) was provided showing that the four directories were created and the assertions passed; thus the requirement cannot be confirmed.
- `T008b` (rejected 1x): The `code/utils/checksum.py` file is truncated (it ends abruptly after `if` in `scan_and_register_data_files`) and does not contain the full logic to compute checksums for files in `data/` and write them to `state/pending/checksums.yaml`. Consequently, the required pending YAML file is also absent. The implementation must be completed and verified to produce the pending checksums file.
- `T007` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T009` (rejected 1x): The repository lacks the required `data/raw/chembl_raw.csv` output, the `state/pending/checksums.yaml` file, and the schema file referenced in the task. Moreover, the provided `code/data/retrieval.py` is truncated and does not show CSV writing or invocation of the checksum utility, so the core functionality is not demonstrably implemented. The missing artifacts must be created and the script completed to meet the specification.
- `T010` (rejected 1x): The repository lacks the required input file `data/raw/chembl_raw.csv`, the output file `data/processed/filtered_data.csv`, and the checksum file `state/pending/checksums.yaml`. Moreover, the provided `code/data/preprocessing.py` is incomplete (truncated) and does not show the logic for filtering, reporting pass rates, saving the filtered CSV, or invoking `code/utils/checksum.py`. These essential artifacts and functionality are missing.
- `T012` (rejected 1x): The `tests/contract/test_dataset.py` file is present but does not show the required `test_schema_compliance` function, and the referenced schema file `specs/.../contracts/dataset.schema.yaml` is missing from the repository. Both the test implementation and the schema file are required to satisfy the task.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

