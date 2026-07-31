# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T016` (rejected 1x): The required `data/processed/config.json` file is missing, so the script cannot read the number of instances (N). Moreover, the provided excerpt of `code/generate_topology.py` does not show the requested batch generation loop over p = 0.0 → 1.0 in 50 steps, so we cannot verify that it has been implemented. Both essential artifacts are absent or incomplete.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

