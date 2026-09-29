# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T008a` (rejected 1x): The provided information contains no view of `research.md`; there is no evidence that the file exists, contains the word “methodology”, or includes the placeholder “[deferred]”. Without the actual file content we cannot confirm the required methodology description was added. The implementer must supply the `research.md` file showing the methodology text and the “[deferred]” marker.
- `T099` (rejected 1x): No content of `research.md` was provided, so we cannot verify that it contains the required “External Oracle” definition or the word “immutable”. The implementer must supply the updated `research.md` file (or its relevant excerpt) showing those entries.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

