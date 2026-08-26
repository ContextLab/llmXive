# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T090` (rejected 1x): The required artifact `data/processed/cue_intensity_weights.json` does not exist, so the cue‑intensity weighting schemes have not been defined or stored as specified. The task therefore remains unfinished.
- `T091` (rejected 1x): declared artifact(s) missing/empty/invalid: data/processed/power_analysis_results.json
- `T093` (rejected 1x): declared artifact(s) missing/empty/invalid: data/manifest.json
- `T050` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/stimuli.csv, data/checksums.json

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

