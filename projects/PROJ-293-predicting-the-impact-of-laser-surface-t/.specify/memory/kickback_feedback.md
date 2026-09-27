# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The repository lacks a `handle_missing_values` function implementing the required dropping/retaining logic, and the expected output file `data/processed/aggregated_clean.csv` does not exist. Consequently the task’s core requirements are not met.
- `T015` (rejected 1x): The required `data/processed/aggregated_clean.csv` file is absent, and `state/artifact_hashes.yaml` contains no entries for the artifact’s checksum, so neither output was produced nor recorded.
- `T014` (rejected 1x): The repository contains `normalized_only.csv`, `raw_only.csv`, and `split_summary.json`, but they are empty (only headers) and the summary reports zero counts instead of the expected split statistics. Moreover, the required source file `data/processed/aggregated_clean.csv` is missing, and the provided `code/ingest.py` excerpt does not show a concrete implementation of `split_dataset`. Consequently the task’s functional and output requirements are not satisfied.
- `T016a` (rejected 1x): The provided `code/ingest.py` does not contain a `count_records` function (the visible portion shows other utilities but no implementation of the required function), and the expected output file `data/processed/record_counts.json` is absent from the repository. Both the core function and its JSON artifact are missing, so the task is not satisfied.
- `T016b` (rejected 1x): The provided `code/ingest.py` does not contain a `compare_thresholds` implementation (the file is truncated and no such function is visible), and the required output file `data/processed/threshold_check.json` is absent. Consequently the task’s behavior—threshold comparison, exit codes, `study_scope` setting, and JSON generation—has not been delivered.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

