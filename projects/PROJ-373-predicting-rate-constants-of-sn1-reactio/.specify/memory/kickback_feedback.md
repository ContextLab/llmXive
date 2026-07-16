# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The exclusion_report.csv file exists and contains the required columns and mapped error codes, but the required schema file (`exclusion_report.schema.yaml`) is missing, so the report cannot be verified to match the specified schema. The task therefore does not meet all requirements.
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/cleaned_sn1.csv
- `T022` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T023` (rejected 1x): No `artifacts/hyperparameter_search.log` file or its contents were provided; thus there is no evidence that the top‑10 hyperparameter configurations and their validation R² scores were logged as required. The implementer must supply the actual log file with the expected entries.
- `T030` (rejected 1x): I looked for the three required files in the repository (`artifacts/feature_importance.png`, `artifacts/sensitivity_report.csv`, and `artifacts/perturbation_results.csv`). None of these artifacts are present, and no content is shown that would satisfy the specified column formats. The task therefore remains unfinished.
- `T033` (rejected 1x): The required deliverable `artifacts/integration_test_report.md` is not present in the provided evidence, nor is any content showing that the full pipeline was executed and verified without error. Without this report, the integration test requirement is unmet.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

