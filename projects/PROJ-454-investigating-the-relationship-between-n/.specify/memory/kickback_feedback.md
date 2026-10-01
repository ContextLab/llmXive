# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): No configuration artifact (e.g., a settings file, environment variable definitions, or code module) that defines and manages dataset URLs and entropy‑threshold values is present. The claim provides only the broader feature specification, but the required environment configuration management artifact is missing.
- `T010` (rejected 1x): The test file `tests/contract/test_dataset_schema.py` is present, but it depends on `specs/001-neural-entropy-cognitive-flexibility/contracts/dataset.schema.yaml`, which is missing; the test will be skipped, so the contract validation is not actually performed. The required schema artifact must be added for the task to be complete.
- `T014` (rejected 1x): The repository lacks the required `data/processed/snr_metrics.json` file, and the shown `code/02_preprocess_eeg.py` is truncated before any SNR calculation logic is completed, indicating the implementation is missing. The task’s output artifact and full calculation are not present.
- `T016` (rejected 1x): The repository contains a partially‑implemented `code/02_preprocess_eeg.py` that stops mid‑function and does not include the required SNR‑based exclusion logic or generation of `exclusion_log.csv`. Moreover, the required input file `data/processed/snr_metrics.json` and the expected output `data/processed/exclusion_log.csv` are absent. The task’s data‑quality checks and output artifact are therefore not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

