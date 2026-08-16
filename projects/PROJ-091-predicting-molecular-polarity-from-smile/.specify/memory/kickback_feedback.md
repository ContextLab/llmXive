# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T035` (rejected 1x): No stability report, Jaccard scores, or log files are present in the provided evidence; the implementer supplied no artifact demonstrating that Jaccard ≥ 0.7 was verified or that failures would be logged for either cluster or individual metrics. The required output is missing.
- `T036` (rejected 1x): No SHAP summary plot, feature‑importance report, or any files distinguishing collinear clusters were supplied. The implementer’s response contains only the task description and project context, without the required visual or data artifacts, so the requirement is not met.
- `T037` (rejected 1x): No files, plots, reports, or SHAP value outputs were presented, and there is no evidence that anything was saved to `data/processed/analysis/`. The required analysis artifacts are missing, so the task is not satisfied.
- `T038a` (rejected 1x): No updated README.md file was presented; the claim provides no evidence of added usage examples or installation instructions, so the required artifact is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

