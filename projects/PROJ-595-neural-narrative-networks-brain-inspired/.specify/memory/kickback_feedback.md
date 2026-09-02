# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/roi_left_hipp.npy
- `T015` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/roi_right_hipp.npy
- `T016` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/roi_dlpfc.npy
- `T019` (rejected 1x): The required output file `data/text/rocstories_sample.jsonl` is missing, so the corpus was not downloaded and sampled as specified. No evidence of a valid JSONL file with `story` and `id` fields is present.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

