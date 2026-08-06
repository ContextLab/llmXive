# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): The `code/schema.py` file exists but is truncated (e.g., `validate_null_values` ends abruptly) and cannot be verified against the required `contracts/dataset.schema.yaml`, which is missing from the repository. Both the schema definition file and a complete implementation are needed to satisfy the task.
- `T018` (rejected 1x): No code, script, or log file was provided that shows learners without forum interactions are being filtered out and that the number excluded is being recorded. The required artifact (implementation of the exclusion logic and logging of the exclusion count) is missing.
- `T019` (rejected 1x): No code, script, or log file was provided that demonstrates the implementation of the exclusion logic for courses with fewer than 50 learners, nor any evidence that the number of excluded courses is being logged. Without such artifacts, the requirement cannot be confirmed as satisfied.
- `T020` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/learners_raw.csv
- `T024` (rejected 1x): No code, notebook, script, or data file implementing the median feedback‑interval calculation per learner is present. The required artifact (e.g., a function or pipeline step that computes each learner’s median interval and assigns them to the “Immediate”, “Delayed”, or “Variable” groups) is missing, so the task’s requirement is not satisfied.
- `T025` (rejected 1x): No code, script, notebook, or any other artifact implementing the required binning logic (assigning learners to “Immediate”, “Delayed”, or “Variable” groups based on median feedback interval) was provided. Without such a concrete implementation or output, the claim that FR‑004 is satisfied cannot be verified. The missing artifact must be supplied for the task to be considered complete.
- `T026` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/learners_binned.csv
- `T035` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/results_metrics.csv
- `T036` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/significance_stability_report.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

