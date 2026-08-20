# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T013` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/mask_paths.json
- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/roi_left_hipp.npy
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/roi_right_hipp.npy
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/roi_dlpfc.npy
- `T019` (rejected 1x): The required output file `data/text/rocstories_sample.jsonl` does not exist, so the ROCStories corpus has not been downloaded and sampled as specified. The task’s core requirement is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

