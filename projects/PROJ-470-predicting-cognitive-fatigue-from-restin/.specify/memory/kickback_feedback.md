# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T009` (rejected 1x): The provided `code/download.py` is truncated and does not contain the full download, manifest‑writing, or sample‑file creation logic; consequently `data/raw/download_manifest.json` and `data/raw/sample_eeg.fif` are absent. Moreover, the script does not implement the required exit‑with‑code‑1 behavior or proper validation of a dataset containing both resting‑state EEG and fatigue ratings. The task therefore remains unfinished.
- `T021` (rejected 1x): The required output file `data/analysis/ancova_results.csv` does not exist, so the verification step cannot be satisfied. Additionally, the provided excerpt of `code/analysis.py` is truncated before any ANCOVA modeling code, leaving it unclear whether the specified model (`Post_Complexity ~ Fatigue_Delta + Pre_Complexity + Covariates`) was actually implemented. Both the artifact and its content are missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

