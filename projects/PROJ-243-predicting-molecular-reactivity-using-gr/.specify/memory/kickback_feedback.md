# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008` (rejected 1x): No `artifacts/logs/` directory with structured log files nor an `artifacts/metrics.json` file is present. The implementer did not provide any code, configuration, or generated output demonstrating that logging has been set up to write to those locations. Consequently, the required logging infrastructure is missing.
- `T009a` (rejected 1x): The required file `data/raw/reference_substructures_raw.csv` does not exist, so the download step was not performed and the artifact is missing. The task’s core requirement is therefore not satisfied.
- `T009b` (rejected 1x): The required file `data/raw/reference_substructures_raw.csv` does not exist, so no SHA-256 checksum can be computed or compared to the source manifest. The task cannot be considered completed until the file is present and its checksum verified.
- `T009c` (rejected 1x): The required artifact `data/assets/reference_substructures.csv` does not exist, so no data ingestion or schema validation could have been performed. The implementer must create the CSV file with the verified data and ensure it conforms to the expected schema.
- `T009d` (rejected 1x): The required artifact `data/raw/kinetic_dataset_raw.csv` does not exist, so the dataset was not downloaded as specified. The task remains undone.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

