# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016` (rejected 1x): No code, log files, or other artifacts were provided that demonstrate the addition of logging for data source selection or the emission of `E_DATA_INSUFFICIENT` warnings in synthetic‑mode fallback. Without concrete files showing the required log format (`LOG: Data source selected: {source} | Rows: {count} | Status: {status}`) the claim cannot be verified. The implementer must supply the updated script/module and example log output confirming the behavior.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

