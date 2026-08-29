# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T025` (rejected 1x): No code, data, or result files (e.g., script implementing the paired t‑test, a CSV of prediction errors, or a report showing the t‑test statistic and p‑value) were provided. Without these artifacts the claim that FR‑007 (paired t‑test on prediction errors between GNN and RF‑Baseline) has been implemented cannot be verified. The missing deliverables need to be added for the task to be considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

