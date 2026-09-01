# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011b` (rejected 1x): No synthetic dataset artifact was supplied; there is no file, code, or description showing that a dataset was generated, nor any evidence that it meets the conditional requirements of the task. The implementer’s claim lacks any tangible output.
- `T011d` (rejected 1x): No ingestion script, validation logs, or output CSV containing the filtered microbiome‑serology dataset is provided, nor are there any correlation analysis results, CLR‑transformed data, Shannon diversity calculations, or predictive‑modeling artifacts (e.g., Random Forest model files, cross‑validation reports). The required deliverables are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

