# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T001` (rejected 1x): No directory tree or file listing was provided to confirm that the required folders (`projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/data/{raw,processed,results}` and `projects/PROJ-800-assessing-parcellation-sensitivity-of-hu/{code,tests}`) actually exist. The implementer’s claim cannot be verified without concrete evidence of the created directories.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

