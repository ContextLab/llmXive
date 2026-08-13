# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T000c` (rejected 1x): No `research/validation_report.json` file or parsing script is present, and there is no evidence that citations were checked for `status="valid"` and `overlap >= 0.7` with error handling on failure. The required artifact and its functionality are missing.
- `T001a` (rejected 1x): No `research.md` file is present in the provided evidence, and there is no content showing the required table with columns Effect Size, Alpha, Target Power, Required N, and Calculated N. The implementer therefore has not delivered the requested template.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

