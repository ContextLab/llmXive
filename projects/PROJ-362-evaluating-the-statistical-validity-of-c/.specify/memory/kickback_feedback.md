# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T017` (rejected 1x): No CSV files were presented or listed in the evidence, and there is no proof that any files exist at `projects/PROJ-362-evaluating-the-statistical-validity-of-c/results/null_distributions/` with the required `query_id, metric, score` headers. The implementer must provide the actual CSV artifacts (or a directory listing with file contents) to satisfy the task.
- `T016` (rejected 1x): No code, scripts, data files, or output (e.g., permutation test results, p‑value tables, CSV summaries, or PNG visualizations) were provided. Consequently, there is no evidence that the required p‑value calculation logic—or any of the associated workflow steps—has been implemented or produces the expected artifacts. The implementer must supply the actual implementation and its generated outputs.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

