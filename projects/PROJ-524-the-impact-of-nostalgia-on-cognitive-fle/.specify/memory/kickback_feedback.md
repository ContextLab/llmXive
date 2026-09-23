# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007` (rejected 1x): No `contracts/` directory or any files within it were provided as evidence, and there is no indication that such a structure was created. The required artifact is missing, so the task is not satisfied.
- `T012e` (rejected 1x): The required output files `data/processed/cleaned_dataset.csv` and `data/processed/cleaned_dataset_no_mmse.csv` are missing, and `exclusion_counts.json` does not record any MMSE‑based exclusions even though the source CSV contains participants with MMSE < 24. The task’s filtering and file‑generation steps have not been performed.
- `T012c` (rejected 1x): The required `data/processed/exclusion_log.json` file is absent, so the exclusion log was never generated. Consequently the task’s core output is missing.
- `T014a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/cleaned_dataset.csv
- `T019` (rejected 1x): No code, script, or documentation implementing a Bonferroni correction for the two metrics (`perseverative_errors` and `categories_completed`) was provided; the evidence consists only of the task description without any tangible artifact. The required implementation artifact is missing.
- `T020` (rejected 1x): No artifact (e.g., script output, report, table, or figure) showing calculated Cohen's d values with their 95 % confidence intervals for the primary comparisons is present. The implementer provided no code, results, or documentation that demonstrates the required effect‑size calculations, so the task is not satisfied.
- `T023` (rejected 1x): No code, script, or documentation was provided that adds error handling for zero variance or insufficient sample size, and there is no artifact path or file to inspect. Consequently, the required implementation is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

