# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T031b` (rejected 1x): The provided `check_pilot_data.py` is truncated (the `check_pilot_data` function ends abruptly) and lacks a runnable entry‑point, so it cannot reliably produce the required exit codes or JSON output. Additionally, the required data file `data/pilot/raw_pilot_data.csv` and schema file `contracts/pilot_data.schema.yaml` are absent, preventing any real validation. The implementation must be completed and the necessary files supplied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

