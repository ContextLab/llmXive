# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T007a` (rejected 1x): No dataset files, download scripts, or checksum validation logs are present; the claim provides no tangible artifact confirming that the CTU dataset was downloaded from the canonical URL or that its checksum was verified. The required evidence is missing.
- `T007b` (rejected 1x): No artifact (downloaded NF‑BoT‑IoT files, checksum file, or validation script/log) is present; the claim provides no evidence that the dataset was retrieved or that its checksum was verified. The required download and checksum validation steps are therefore missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

