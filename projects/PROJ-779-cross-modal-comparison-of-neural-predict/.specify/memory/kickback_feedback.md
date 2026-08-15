# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T022` (rejected 1x): The `data/processed/cleaned_data.fif` artifact does not exist, and the provided `code/data/preprocess.py` (as shown) contains only preprocessing functions with no code that writes the cleaned data to that path or logs trial rejection. The required output file and saving behavior are missing.
- `T030` (rejected 1x): The repository contains a `metrics.py` file, but it is truncated and does not show any implementation that extracts mean amplitude for the specified windows or writes a `data/results/metrics_summary.json` file. Moreover, the required JSON output file is missing entirely. The task’s core deliverables are therefore not present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

