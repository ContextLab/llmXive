# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T035` (rejected 1x): No updated `quickstart.md` or `research.md` files were provided or referenced; the evidence lacks any documentation changes, so the required artifacts are missing.
- `T036` (rejected 1x): No code files, commit diffs, or documentation showing that the data loading logic was cleaned up or refactored are present. Without any artifact to inspect, we cannot confirm that the required refactoring was performed. The implementer must provide the updated source code (e.g., a cleaned `data_loader.py` or equivalent) and evidence that it replaces the previous implementation.
- `T037` (rejected 1x): The submission contains only the task description and no actual artifacts such as a data‑processing script, generated CSV files with token‑level features and RTPurbo labels, a trained static predictor model or derived rule set, nor any evaluation results or statistical analysis. Consequently, the required outputs for User Stories 1‑3 are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

