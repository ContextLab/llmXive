# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014` (rejected 1x): The repository contains `code/data/preprocess.py`, but it only builds a tiny hard‑coded canonical map and writes a placeholder JSON (`canonical_map_size` etc.) to a path derived from `processed_dir.parent`, not to the required `data/normalization_config.json` (which is missing). No actual mapping or exclusion counts are logged, and the script does not process real Recipe1M ingredient data. The required output file is absent, so the normalization step is not genuinely implemented.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

