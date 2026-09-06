# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T006` (rejected 1x): No code files, scripts, or documentation for MD5/SHA256 checksum utility functions were presented, nor any `artifacts/checksums.txt` or related test showing the functions enforce the protocol. The required artifact is missing, so the task is not satisfied.
- `T007` (rejected 1x): No seed‑management module or script is present in the provided evidence; there is no importable utility, documentation, or example showing how a random seed is set and propagated across analysis scripts. The required artifact is missing, so the task is not satisfied.
- `T008` (rejected 1x): declared artifact(s) missing/empty/invalid: preprocess.yaml

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

