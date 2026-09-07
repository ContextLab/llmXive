# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T018` (rejected 1x): No artifact (e.g., modified script, added try/except around radon calls, log output, or updated dataset generation code) was presented to demonstrate that radon failures are now caught, logged, and excluded. Without such evidence the requirement is not satisfied.
- `T019` (rejected 1x): The `syntax_validator.py` script exists, but the required output file `data/processed/syntax_validation_report.json` is not present, indicating the validation report was never written. The task’s core deliverable—a JSON report confirming ≥95% syntax validity or reporting generation failure—is missing.
- `T022` (rejected 1x): The `code/analysis/matching.py` file exists and implements propensity‑score matching using the specified covariates, but the required data artifact `data/processed/classified_snippets.parquet` is missing, so the module cannot be executed as intended. The missing parquet file must be provided for the task to be complete.
- `T023b` (rejected 1x): The required `data/processed/matching_failure_report.json` file does not exist, and the provided `code/analysis/matching.py` snippet shows no implementation of retry logic, SMD‑threshold checking, or report generation as specified. The task’s core requirement is therefore unmet.
- `T032` (rejected 1x): No PDF or HTML report was supplied, and there are no files containing the required p‑value, effect size, or visualizations. The implementer provided no tangible artifact to verify that a report generation feature was built. The missing deliverable is a generated report (PDF/HTML) that includes the statistical results and accompanying figures.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

