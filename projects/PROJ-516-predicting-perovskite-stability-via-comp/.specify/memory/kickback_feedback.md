# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T004` (rejected 1x): No `state_manager.py` file was presented, and there is no evidence that SHA‑256 hashes are being computed for derived artifacts or that any `state/...yaml` files have been updated. The required artifact is missing, so the task is not satisfied.
- `T012a` (rejected 1x): declared artifact(s) missing/empty/invalid: data/raw/nrel_perovskites.csv

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

