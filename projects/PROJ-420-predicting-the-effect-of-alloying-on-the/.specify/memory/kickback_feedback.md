# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The `clean.py` file shows no code that checks for a missing `measurement_method`, attempts inference, or calls the T016 logging utility; the file is truncated before any such logic could appear. Additionally, the required `data/logs/exclusion_log.txt` does not exist, so exclusions cannot be recorded. The task’s core functionality is therefore not implemented.
- `T015` (rejected 1x): The repository contains a partially shown `code/data/clean.py` that ends abruptly and does not demonstrate the required final orchestration (reading the exclusion log, counting rows, halting on <50, and writing the parquet file). Moreover, the expected output files `data/logs/exclusion_log.txt` and `data/processed/alloys_clean.parquet` are absent. The task’s core requirements are therefore not satisfied.
- `T046` (rejected 1x): The `code/cli/clean_cli.py` script exists and correctly defines the required flags, but the expected output artifact `data/processed/alloys_clean.parquet` is missing, so the task’s requirement of producing that Parquet file is not satisfied. The implementer must provide the generated Parquet file (or a valid placeholder) at the specified location.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

