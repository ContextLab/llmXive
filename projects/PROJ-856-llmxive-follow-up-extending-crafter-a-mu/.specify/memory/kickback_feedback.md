# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T005` (rejected 1x): The three required source modules and the unit‑test file are present and implement the dual‑success logic correctly, but the referenced `semantic_validation.schema.yaml` is missing, so we cannot verify that the generated records actually conform to the required schema. Adding the schema file (or otherwise proving conformance) is needed to complete the task.
- `T008` (rejected 1x): Requested task execution failed; rerun successfully: src/analysis/wilcoxon_analysis.py exit=2

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

