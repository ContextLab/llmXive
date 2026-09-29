# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T071b` (rejected 1x): No evidence of `state/validation_log.json` or `state/research_validated.lock` was provided; the implementer did not show that the Reference-Validator Agent was run, that the log file exists with an `'all_valid'` status, nor that the required lock file was created. These artifacts are mandatory for task completion.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

