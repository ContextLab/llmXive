# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T003a` (rejected 1x): declared artifact(s) missing/empty/invalid: ruff.toml
- `T017c` (rejected 1x): The required output file `data/interim/human_pilot_cleaned.csv` does not exist, and the provided `code/annotation.py` snippet neither shows logic that enforces an exact “<80% agreement on control items” rule nor writes the cleaned DataFrame to the specified path. The deliverable is missing, so the task is not satisfied.
- `T017e` (rejected 1x): The required output `data/results/feature_validation_report.md` does not exist, so the pipeline’s validation gate cannot produce the required Pass/Fail report. Without this file the task’s deliverable is incomplete.
- `T017h` (rejected 1x): The required output file `data/results/contingency_report.md` does not exist, and the provided snippet of `code/annotation.py` does not show any logic that writes a failure report to that path or aborts the pipeline as specified. The implementation therefore does not satisfy the task’s requirement.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

