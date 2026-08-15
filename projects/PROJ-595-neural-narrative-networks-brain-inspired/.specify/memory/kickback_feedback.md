# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: data/neural/processed/roi_timecourses.csv
- `T014` (rejected 1x): No code, script, or documentation implementing chunked loading/subsampling for large fMRI datasets is present; the only evidence is the task description itself, with no concrete artifact to verify the feature. The required implementation and any associated tests or usage examples are missing.
- `T015` (rejected 1x): The required output file `data/text/rocstories_sample.jsonl` does not exist, so the ROCStories corpus has not been downloaded and sampled as specified. The implementer must create this JSONL file with a representative subset of stories in the indicated path.
- `T016` (rejected 1x): No validation script or code was provided that checks for corrupted or incomplete data and aborts with specific error messages. The required artifact (e.g., a Python/ Bash validation step integrated into the data pipeline) is missing, so the task’s requirement is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

