# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T021` (rejected 1x): The implementer supplied only a high‑level feature description and user stories; there is no evidence of any changes to `detect_threshold.py`, no code, tests, or output demonstrating handling of small bin sizes. The required artifact (updated script handling small bins) is missing.
- `T022` (rejected 1x): The response contains only the task description and no actual artifacts such as the annotated dataset, summary table, statistical test results, or the required plots. Consequently, there is no evidence that the summary table and visualizations were generated, so the requirement is not satisfied.
- `T026` (rejected 1x): No comparison table (or any other output) was provided; the response contains only the task description and no concrete artifact such as a CSV/markdown table showing accuracy or other metrics across hop thresholds. The required deliverable is missing.
- `T027` (rejected 1x): No overlay plot or any data/analysis artifacts were provided; the claim contains only the task description and specifications, with no figure, code, or results to verify that accuracy curves for different threshold definitions were actually created. The required overlay plot is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

