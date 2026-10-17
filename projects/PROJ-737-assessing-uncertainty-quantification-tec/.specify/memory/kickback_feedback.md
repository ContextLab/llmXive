# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): The schema YAML correctly lists the eight required columns and the test script passed (exit 0), but `quickstart.md` contains a placeholder for a required fact: the training cap reads "**[deferred] samples**" instead of documenting the 2000-sample cap. The task explicitly requires the document to state the 2000-sample training cap, so this is an unmet requirement that must be fixed.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

