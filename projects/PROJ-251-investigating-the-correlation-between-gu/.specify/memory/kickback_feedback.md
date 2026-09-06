# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011b` (rejected 1x): No synthetic dataset file or code to generate one was provided; the evidence contains only the original user story specifications, with no actual dataset, script, or description of how the synthetic data was created. The required artifact (a non‑empty synthetic dataset) is missing.
- `T011d` (rejected 1x): No code, data files, or result artifacts (e.g., ingestion script, cleaned CSV, correlation tables, adjusted p‑values, Shannon index calculations, or modeling outputs) were provided. Without these concrete outputs, we cannot confirm that the required data ingestion, validation, correlation analysis, multiple‑testing correction, or predictive modeling were actually implemented. The next implementer must supply the relevant scripts and generated result files.
- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: schema.yaml
- `T032` (rejected 1x): No ingestion script, data validation logs, correlation analysis results, or modeling code/output were provided. The required artifacts (e.g., CSV of filtered subjects, Spearman correlation table with raw and BH‑adjusted p‑values, Shannon diversity calculations, and nested‑CV Random Forest performance metrics) are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

