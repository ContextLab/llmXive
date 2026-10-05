# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T021` (rejected 1x): The repository contains a partially‑written `code/statistical_analysis.py` that is truncated and never writes `data/merged_analysis.json`. Moreover, the required source files `data/static_baseline.csv` and `data/processed/semantic_results.json` are absent, so the script cannot perform the merge nor produce the specified JSON output. The deliverable is therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

