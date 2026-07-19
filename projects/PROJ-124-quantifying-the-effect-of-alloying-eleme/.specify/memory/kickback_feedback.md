# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008a` (rejected 1x): No configuration artifact (e.g., a YAML/JSON settings file, .env template, or code that centralizes dataset URLs and random seed handling) is present in the provided evidence. The only artifacts described relate to data ingestion, feature engineering, and model training, which do not satisfy the requirement to configure environment configuration management for dataset URLs and random seeds. The implementer must add a concrete configuration solution (e.g., a config module or file) that defines and loads these parameters.
- `T012` (rejected 1x): The provided `code/data/download.py` does not meet the specification: it uses `datasets.load_dataset` instead of `huggingface_hub.hf_hub_download` or `requests`, the retry logic (`MAX_RETRIES`) is never applied, there is no explicit 401/403 handling, it points to a different HuggingFace repo (`ml4matscience/gfa-experimental`), and it never calls `verify_schema` nor generates the checksum with `code/data/checksums.py` after verification. Consequently the required output files `data/raw/gfa_dataset.csv` and its `.sha256` checksum are missing. The script must be revised to use the correct dataset

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

