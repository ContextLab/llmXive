# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T011d` (rejected 1x): No merge script, function, or resulting merged dataset was presented; there is no file or code that demonstrates merging the OTU table with serology metadata on `subject_id`. Consequently, the required artifact is missing, so the task is not satisfied.
- `T020c` (rejected 1x): The repository lacks the required `data/processed/cleared_with_diversity.csv` file, so the script cannot read the input data. Moreover, the provided `code/02_preprocess.py` (even in the visible portion) contains only loading, zero‑variance exclusion, and normalization logic; there is no implementation that computes the Shannon diversity index or adds it to the output. Both the necessary data artifact and the core functionality are absent.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

