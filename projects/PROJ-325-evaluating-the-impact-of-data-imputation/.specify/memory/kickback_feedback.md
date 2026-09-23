# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): The provided `loader.py` is truncated and does not contain a `fetch_survey_data()` implementation, nor does it show the required logic for URL fetching, caching, column checks, row subsetting, or manifest updates. Additionally, the expected output files `data/raw/gss_2018_subset.csv` and `state/manifest.yaml` are absent. The task therefore remains unfinished.
- `T020` (rejected 1x): The repository contains a `write_baseline_summary` function, but the script’s entry point (argument parsing and execution for `--stage=baseline`) is truncated and does not show that it writes to `data/processed/baseline_results.json`. Moreover, the required JSON file is absent from the project. The task’s verification step cannot be performed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

