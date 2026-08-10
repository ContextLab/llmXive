# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T024a` (rejected 1x): The repository lacks the required `data/processed/samples_all.csv` and the resulting `data/processed/metrics_all.csv`. Moreover, `code/analysis/metrics.py` is truncated and contains no logic to read the “all samples” CSV, compute per‑task/style mean AST and entropy, and write the aggregated metrics file. These essential artifacts are missing, so the task is not fulfilled.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

