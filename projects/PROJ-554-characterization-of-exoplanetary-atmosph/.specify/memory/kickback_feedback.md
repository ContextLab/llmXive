# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/metadata.csv
- `T013a` (rejected 1x): The repository lacks a `count_unique_planets` implementation in `code/download.py` (the shown file ends before any such function) and the required output file `data/processed/count_report.json` does not exist. Both the core function and its deliverable are missing.
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/retrieval_results.csv
- `T030a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/correlation_stats.json
- `T031` (rejected 1x): The repository lacks the required `results/power_analysis.json` and `results/quality_report.md` files, and the `code/analysis.py` does not contain a completed `calculate_statistical_power` implementation (the function is absent/truncated). These missing artifacts mean the task’s deliverables are not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

