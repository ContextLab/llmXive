# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T015` (rejected 1x): The repository lacks the required `data/processed/cleaned_eeg.fif` input and the resulting `data/processed/lzc_metrics.csv` output file. Moreover, `code/features.py` does not contain the full pipeline that iterates over participants, computes LZC per channel, and writes the CSV with the specified schema. These essential artifacts are missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

