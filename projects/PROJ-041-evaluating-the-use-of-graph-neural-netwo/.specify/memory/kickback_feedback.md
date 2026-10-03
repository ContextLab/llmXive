# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): The required output files `data/processed/train_split.csv`, `data/processed/test_split.csv`, and `data/processed/graph_train_split.graphml` are absent from the repository, so the temporal holdout split and graph construction have not been performed. No other artifacts were provided to demonstrate that the split logic or graph creation was executed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

