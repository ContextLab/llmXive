# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T123` (rejected 1x): No ruff check output, log, or summary report is present to demonstrate that the codebase was linted and that the number of warnings is ≤ 5. The required artifact proving the linting result is missing.
- `T124` (rejected 1x): No evidence of a `black --check` run (e.g., command output, log file, or report) is present, nor any indication that the codebase was verified to be correctly formatted. The required artifact confirming the formatting check is missing.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

