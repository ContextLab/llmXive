# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): No evidence of a `01_data_acquisition.py` script, its download logic, checksum verification via `utils/validators.py`, or the presence of raw files in `data/raw/` was provided. The required artifact is missing, so the task is not satisfied.
- `T015` (rejected 1x): No `01_data_acquisition.py` file or its contents were provided, and therefore we cannot confirm that any stratified sampling or shuffling operations are pinned with `random_state=42`. The required artifact is missing.
- `T016` (rejected 1x): No `02_preprocessing.py` file or any related code, data, or logs were provided; therefore the required preprocessing implementation (downloading datasets, validating columns, sampling, and logging exclusions) is missing. The claim cannot be verified without the actual artifact.
- `T017` (rejected 1x): No evidence was provided showing a `data/processed/` directory containing the preprocessed datasets, nor a `state/projects/...yaml` file with recorded SHA‑256 checksums. Both the processed data files and the checksum YAML are required to satisfy task T017.
- `T018` (rejected 1x): No code, script, or log files were provided showing the FR‑008 disclaimer added to console output or log messages of the US1 scripts. Without concrete artifacts (e.g., modified source files, example console output, or log excerpts containing the disclaimer), we cannot verify that the requirement was fulfilled. The implementer must supply the updated scripts and sample outputs demonstrating the disclaimer.
- `T019` (rejected 1x): No script, log file, or any output showing SHA‑256 hashes computed before and after processing is present; therefore the required verification of raw data integrity is not demonstrated. The implementer must provide the hashing code and evidence (e.g., a report or logs) that hashes are recomputed and unchanged for each raw file.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

