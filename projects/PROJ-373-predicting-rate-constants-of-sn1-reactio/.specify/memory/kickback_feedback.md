# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The required input `data/processed/intermediate_sn1.csv` and the expected outputs (`clean.log` and `cleaned_intermediate.csv`) are absent, so the script cannot run or produce the mandated files. Moreover, the provided `clean.py` is incomplete, raises a `FileNotFoundError` instead of the specified fatal `ValueError` with the exact log format, and contains a proxy‑based steric index calculation, violating the “no proxies” constraint. The implementation therefore does not satisfy the task requirements.
- `T013` (rejected 1x): The repository contains `code/data/descriptors.py`, but the required output file `data/processed/descriptors.csv` does not exist, and the exclusion log `data/processed/exclusion_raw.log` contains only the header with no logged failures. Hence the implementation does not fulfill the task’s output and logging requirements.
- `T040` (rejected 1x): No execution logs, generated artifacts, or the required `artifacts/feasibility_test_log.json` (or any other validation output) were provided. Without these files we cannot confirm that the pipeline was re‑run, that schemas were checked, or that any timeout/abortion was documented, so the task’s validation requirement is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

