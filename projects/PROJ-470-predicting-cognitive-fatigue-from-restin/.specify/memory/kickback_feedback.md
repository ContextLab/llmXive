# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T010` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/validation_report.json
- `T012a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/download_manifest.json, data/raw/sample_eeg_verification.fif
- `T016` (rejected 1x): The required output file `data/analysis/complexity_metrics.csv` does not exist, and the input EEG file `data/processed/cleaned_eeg.fif` is also missing. Moreover, `code/features.py` is truncated and incomplete (ends abruptly), so it cannot reliably generate the needed CSV. These missing/unfinished artifacts prevent the task from being satisfied.
- `T018` (rejected 1x): The provided `code/analysis.py` validates different files (VIF JSON, delta_scores.csv) and never checks for `data/processed/cleaned_eeg.fif` or `data/processed/fatigue_scores.csv`. Moreover, none of the three required data files exist in the repository. The implementation therefore does not satisfy the task’s validation logic or the existence requirement.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

