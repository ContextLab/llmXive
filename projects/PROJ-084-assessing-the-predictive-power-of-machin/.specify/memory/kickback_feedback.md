# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016` (rejected 1x): The repository contains `code/preprocessing/fingerprints.py`, which implements fingerprint generation and chunked processing, but the required log file `data/results/fingerprint_dimensions.log` is absent, and there is no evidence that the script writes the actual bit lengths (2048 and 167) to that file or includes them in a data quality report. The task’s logging requirement is therefore unmet.
- `T019` (rejected 1x): The provided `download.py` defines verification and utility functions but the code for actually streaming the dataset, writing it to `data/raw/uspto_raw.parquet`, computing the SHA256 checksum, and logging it to `data/results/download_checksum.txt` is absent (truncated) and the expected output files are missing. Implement the download, parquet write, checksum calculation, and logging steps so the script fulfills the full task specification.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

