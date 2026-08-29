# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T014b` (rejected 1x): No Python wrapper script, command‑line integration, XML parsing logic, or syntax‑validation code was provided. The required artifact (a functional script that runs `pmd -f xml -d <dir> -rulesets rulesets/java/complexity.xml`, parses `<violation>` tags, and validates Java files) is missing, so the task is not satisfied.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

