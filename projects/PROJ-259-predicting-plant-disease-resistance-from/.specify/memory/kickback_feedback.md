# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T042` (rejected 1x): The provided `code/data/download.py` does not show the required critical‑warning log message nor an explicit immediate call to `generate_synthetic.py`, and the mandatory `data_manifest.yaml` file is absent, so the provenance update (`source: SIMULATED`) cannot be verified.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

