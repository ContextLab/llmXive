# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T033` (rejected 1x): The provided `update_bkt_params.py` is truncated (ends mid‑function) and does not show the logic that writes the adjusted parameters back to `code/simulate/bkt_params.yaml`. The existing `bkt_params.yaml` contains only static default values, with no indication it was updated based on calibration metrics. A complete implementation and a demonstrably updated YAML file are required.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

