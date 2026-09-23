# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T043` (rejected 1x): No code, configuration, tests, or documentation showing that T012 was extended to verify streamed data integrity or compute hashes is present. The only artifacts described relate to generating teacher routing data and training decision trees, which do not address the required data‑source verification feature. The required implementation and evidence are missing.
- `T044` (rejected 1x): No code, configuration, log output, or documentation was provided showing that T013b was refined to log and handle undefined expert routing paths. The required artifact (implementation of explicit handling and logging) is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

