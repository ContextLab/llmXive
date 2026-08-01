# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T042` (rejected 1x): The provided `code/data/validate.py` is truncated and never writes `results/validation_report.json` nor implements the required exit‑code logic based on the invalid‑ratio threshold. Moreover, the expected `results/validation_report.json` file is absent. The task’s core output and behavior are therefore not satisfied.
- `T022a` (rejected 1x): The required output file `data/features/test_grain_features.csv` is missing, and the provided `extract_features.py` script is truncated (ends mid‑line) and does not demonstrably implement the full extraction logic limited to the test set. The task’s core deliverable is therefore not present.
- `T024` (rejected 1x): The provided `code/eval/metrics.py` only defines loading, MSE, and R² functions; the snippet shows no implementation of the single‑sample t‑test nor any code that writes `results/statistical_test.json`. Moreover, the required `results/statistical_test.json` file does not exist. The task’s core requirement is therefore unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

