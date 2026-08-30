# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): The provided `code/data/loader.py` only parses arguments and calls external helper functions; it does not enforce the required URL, perform cache fallback, verify the `weight`, `psu`, and `strata` columns, abort on missing columns, or log to `state/manifest.yaml`. Moreover, the expected output files (`data/raw/cache/GSS2018.dta`, `data/raw/gss_2018_subset.csv`, and `state/manifest.yaml`) are absent. The task’s core functional and artifact requirements are therefore not met.
- `T004b` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/gss_2018_subset.csv, state/manifest.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

