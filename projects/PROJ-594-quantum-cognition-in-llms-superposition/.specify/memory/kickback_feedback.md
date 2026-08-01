# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T012` (rejected 1x): The provided `run_baseline.py` is truncated, never writes `baseline_metrics.json`, and does not compute or store variance fields nor enforce the < 0.02 variance check. Moreover, the required `config.yaml` is missing, so seeds cannot be read from configuration as specified. The framing utilities exist but are not demonstrated in the final output. These missing pieces must be added for the task to be considered complete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

