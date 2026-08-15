# Re-plan: task(s) could not be made to pass verification — adjust the approach

The implementer repeatedly failed the verification checks for the task(s) below. They were NOT force-accepted (that fail-open was removed in issue #1139); instead the project re-plans so a DIFFERENT approach (simpler method, different tooling, or a decomposition into individually verifiable steps) can produce checkable artifacts.

## Repeatedly-unverifiable tasks

- `T210` (rejected 1x): No updated `research.md` file is provided; there is no evidence that the scope boundaries (out‑of‑scope physical validation, QM DFT reference data, and exclusion of conformational ensembles/hydration sampling) have been documented as required. The implementer must supply the modified `research.md` containing the explicit statements.

## Required change

Re-plan so each promised deliverable is produced by a step whose output can be deterministically verified (a real file with the expected schema/content). Avoid the approach that produced the unverifiable work above.

