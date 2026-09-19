# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The repository lacks the required `data/processed/total_records_count.json` and `data/processed/metrics.json` files, and the shown portion of `code/data/clean.py` does not contain any logic that loads those files, computes a merged/total coverage rate, or writes the result to `metrics.json`. Consequently the task’s core requirement is not met.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

