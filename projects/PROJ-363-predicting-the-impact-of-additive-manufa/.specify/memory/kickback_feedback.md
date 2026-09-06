# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016b` (rejected 1x): The required output files `data/processed/X_raw.csv` and `data/processed/X_derived.csv` are absent, and the provided `code/preprocess.py` excerpt shows no logic that creates and writes those distinct feature subsets. The implementation therefore does not fulfill the task’s requirement.
- `T017b` (rejected 1x): The `code/preprocess.py` file exists and contains validation logic, but the required `contracts/dataset.schema.yaml` schema file is missing, so the script cannot actually validate against the specified schema. Additionally, there is no evidence (tests, logs, or example runs) showing that validation succeeds on clean data and fails on malformed data. Both the missing schema and lack of verification mean the task is not fully satisfied.
- `T035` (rejected 1x): The repository contains `code/analyze_explainability.py`, but the shown code does not implement the required separate‑model comparison, Spearman correlation calculation, side‑by‑side bar chart, or generation of `results/reports/feature_comparison.json`. Moreover, the expected JSON report file is missing from the results directory. The task’s core output is therefore not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

